#!/usr/bin/env python3
"""Fail closed if recorded Silicon Labs router/lightcore evidence drifts."""
import json
from pathlib import Path
import re
import sys

MANIFEST = Path("firmware/silabs_router_v0_build_manifest.json")
PROFILE = Path("firmware/router_profile.slcp.fragment.yaml")
TUYA_REFERENCE = Path("firmware/reference_build_manifest.json")
ADAPTER = Path("firmware/app/hallbulb_zcl_adapter.c")
APP_DIR = Path("firmware/app")
LIGHT_CORE = Path("firmware/app/hallbulb_light_state.c")
OVERLAY_TOOL = Path("tools/apply_silabs_light_core.py")
ENDPOINT_PROFILE = Path("firmware/endpoint_profile.json")
ENDPOINT_TOOL = Path("tools/apply_silabs_endpoint_profile.py")
ENDPOINT_VERIFY = Path("tools/verify_endpoint_profile.py")

m = json.loads(MANIFEST.read_text(encoding="utf-8"))
profile = PROFILE.read_text(encoding="utf-8")
tuya_reference = json.loads(TUYA_REFERENCE.read_text(encoding="utf-8"))
endpoint_profile = json.loads(ENDPOINT_PROFILE.read_text(encoding="utf-8"))
errors = []


def require(condition, message):
    if not condition:
        errors.append(message)


require(m.get("schema_version") == 3, "Silabs build manifest schema must be 3")
require(m.get("status") == "BUILT_STRUCTURAL_REFERENCE", "status must remain structural-reference build")
require(m.get("deployment_eligible") is False, "structural build must not be deployment eligible")
require(m["target"]["soc"] == "EFR32MG21A020F1024IM32", "unexpected structural compile target")
require(m["target"]["role"] == "router", "target role must remain router")
require(m["sdk"]["version"] == "2026.6.1", "Simplicity SDK version drift")
require(m["sdk"]["zigbee_stack"] == "9.1.1", "Zigbee stack version drift")
require(m["sdk"]["slc_version"] == "6.0.23", "SLC version drift")
require(m["sdk"]["cmake_version"] == "3.30.2", "build CMake version drift")
require(m["sdk"]["ninja_version"] == "1.12.1", "Ninja version drift")
require(m["sdk"]["compiler_version"] == "14.2.1", "compiler version drift")

rp = m["router_profile"]
expected = {
    "neighbor_table": 26,
    "route_table": 16,
    "discovery_table": 8,
    "address_table": 12,
    "broadcast_table": 15,
}
for key, value in expected.items():
    require(rp.get(key) == value, f"router profile {key} must be {value}")
    require(str(value) in profile, f"reviewed router profile missing value {value} for {key}")
require(rp.get("concentrator") is False, "concentrator must remain disabled")
require(rp.get("periodic_many_to_one_originator") is False, "periodic MTORR originator must remain disabled")

g = m["generation"]
require(g.get("source") == "official_vendor_template", "generation must start from vendor template")
require(g.get("no_guessed_gpio") is True, "GPIO guessing must remain forbidden")
require(g.get("direct_from_template_rebuild_success") is True, "direct vendor-template rebuild not proven")
require(g.get("deterministic_bin_match") is True, "deterministic router-v0 BIN match not proven")
require(set(g.get("remove_components", [])) == {"simple_led", "simple_button"}, "dev-board LED/button removals must remain explicit")
require(g.get("configuration") == {"SL_ZIGBEE_NEIGHBOR_TABLE_SIZE": 26}, "router-v0 may only override neighbor table")
ref = m["reference_build"]
rtr = m["router_v0_build"]
require(ref.get("success") is True and rtr.get("success") is True, "reference/router-v0 builds must be successful")
require(ref.get("neighbor_table") == 16 and rtr.get("neighbor_table") == 26, "neighbor-table baseline/delta mismatch")
require(ref.get("bin_bytes") == rtr.get("bin_bytes") == 305244, "unexpected router BIN size drift")
require(rtr.get("bin_sha256") == rtr.get("rebuild_bin_sha256"), "router-v0 clean rebuild hash mismatch")

d = m["router_delta"]
require(d.get("neighbor_entries") == 10, "router-v0 must add exactly 10 neighbor entries")
require(d.get("neighbor_data_bytes") == 180, "neighbor-data RAM delta must remain 180 bytes")
require(d.get("frame_counter_table_bytes") == 40, "frame-counter RAM delta must remain 40 bytes")
require(d.get("bss_section_bytes") == 216, "aligned BSS delta must remain 216 bytes")
require(d.get("managed_heap_bytes") == -216, "managed heap must compensate BSS by 216 bytes")
require(d.get("text_section_bytes") == 0, "router-v0 must not grow .text")
require(d.get("data_section_bytes") == 0, "router-v0 must not grow .data")
require(d.get("bin_bytes") == 0, "router-v0 BIN size must not grow")
require(rtr["bss_section_bytes"] - ref["bss_section_bytes"] == 216, "router BSS values do not reconcile")
require(rtr["managed_heap_bytes"] - ref["managed_heap_bytes"] == -216, "router heap values do not reconcile")

light = m["lightcore_build"]
expected_light_hash = "2ca1d42aca7d1b5bc47cdeb460ff2f74e25f1a1108c1a1b13531b3d9fc412ba6"
require(light.get("success") is True, "lightcore ARM build must be successful")
require(light.get("board_output_implementation") == "weak_noop", "physical board output must remain weak no-op")
require(light.get("no_guessed_gpio") is True, "lightcore must remain board-neutral")
require(light.get("state_contract_exact_zcl_mirror") is True, "lightcore must mirror ZCL state exactly")
require(light.get("minimum_duty_translation_in_core") is False, "minimum-duty translation must stay out of logical core")
require(light.get("board_output_runtime_exercised") is False, "structural weak-noop build must not claim physical output execution")
require(light.get("bin_bytes") == 305468, "lightcore BIN size drift")
require(light.get("text_section_bytes") == 300896, "lightcore .text size drift")
require(light.get("data_section_bytes") == 3984, "lightcore .data size drift")
require(light.get("bss_section_bytes") == 14836, "lightcore .bss size drift")
require(light.get("managed_heap_bytes") == 74968, "lightcore managed heap drift")
for key in ("bin_sha256", "rebuild_bin_sha256", "independent_template_bin_sha256"):
    require(light.get(key) == expected_light_hash, f"lightcore {key} drift")
require(light.get("independent_template_byte_equal") is True, "independent template rebuild must be byte-equal")

ld = m["lightcore_delta_from_router_v0"]
require(ld == {
    "text_section_bytes": 224,
    "data_section_bytes": 0,
    "bss_section_bytes": 0,
    "managed_heap_bytes": 0,
    "bin_bytes": 224,
}, "lightcore delta must remain +224 B text/BIN and zero RAM")
require(light["bin_bytes"] - rtr["bin_bytes"] == 224, "lightcore BIN delta does not reconcile")
require(light["text_section_bytes"] - rtr["text_section_bytes"] == 224, "lightcore text delta does not reconcile")

repro = m["lightcore_reproduction"]
require(repro.get("source") == "official_vendor_template", "lightcore reproduction must start at official template")
require(repro.get("seed_generation") == "slc_new_project", "independent seed must use SLC new-project")
require(set(repro.get("remove_components", [])) == {"simple_led", "simple_button"}, "board-only exclusions must remain explicit")
require(repro.get("configuration") == {"SL_ZIGBEE_NEIGHBOR_TABLE_SIZE": 26}, "lightcore reproduction router override drift")
require(repro.get("seed_overlay_tool") == "tools/apply_silabs_light_core.py", "unexpected lightcore overlay tool")
require(repro.get("generated_header_staging_required") is True, "generated header staging evidence must remain explicit")
require(repro.get("board_only_component_autoselection_detected") is True, "dev-board autoselection finding must remain recorded")
require(repro.get("board_only_component_autoselection_fail_closed") is True, "dev-board autoselection must fail closed")
require(repro.get("independent_clean_build_success") is True, "independent clean ARM build must remain proven")
require(repro.get("independent_byte_equal") is True, "independent source-to-artifact reproduction must be byte-equal")

endpoint = m["endpoint_v0_build"]
expected_endpoint_hash = "b9cd57674051d9239489f639f017b5be112329743ce861ca9f84ae82ba573042"
require(endpoint.get("success") is True, "endpoint-v0 ARM build must be successful")
require(endpoint.get("endpoint_id") == 1, "endpoint-v0 must expose endpoint 1")
require(endpoint.get("profile_id") == 0x0104, "endpoint-v0 HA profile drift")
require(endpoint.get("device_type") == 0x010D, "endpoint-v0 device type must remain Extended Color Light")
require(endpoint.get("server_clusters") == [0, 3, 4, 5, 6, 8, 768, 4096], "endpoint-v0 server cluster drift")
require(endpoint.get("client_clusters") == [10, 25], "endpoint-v0 client cluster drift")
require(endpoint.get("basic_manufacturer_name") == "_TZ3210_mja6r5ix", "endpoint-v0 Basic manufacturer drift")
require(endpoint.get("basic_model_id") == "TS0505B", "endpoint-v0 Basic model drift")
require(endpoint.get("zcl_manufacturer_code_metadata") == 0x100B, "endpoint-v0 ZCL manufacturer metadata drift")
require("not proof" in endpoint.get("zcl_manufacturer_code_metadata_scope", "").lower(), "ZAP manufacturer-code scope must remain non-deployment evidence")
require(endpoint.get("ota_identity_runtime_pending") is True, "endpoint-v0 must not claim resolved OTA runtime identity")
require(endpoint.get("board_output_implementation") == "weak_noop", "endpoint-v0 physical output must remain weak no-op")
require(endpoint.get("deployment_eligible") is False, "endpoint-v0 must remain non-deployable")
require(endpoint.get("bin_bytes") == 304440, "endpoint-v0 BIN size drift")
require(endpoint.get("text_section_bytes") == 299916, "endpoint-v0 .text size drift")
require(endpoint.get("data_section_bytes") == 3936, "endpoint-v0 .data size drift")
require(endpoint.get("bss_section_bytes") == 14192, "endpoint-v0 .bss size drift")
require(endpoint.get("managed_heap_bytes") == 75660, "endpoint-v0 heap size drift")
require(endpoint.get("bin_sha256") == expected_endpoint_hash, "endpoint-v0 BIN hash drift")
require(endpoint.get("independent_template_bin_sha256") == expected_endpoint_hash, "endpoint-v0 independent hash drift")
require(endpoint.get("independent_template_byte_equal") is True, "endpoint-v0 independent build must be byte-equal")

ed = m["endpoint_v0_delta_from_lightcore"]
require(ed == {
    "text_section_bytes": -980,
    "data_section_bytes": -48,
    "bss_section_bytes": -644,
    "managed_heap_bytes": 692,
    "bin_bytes": -1028,
}, "endpoint-v0 delta from lightcore drift")
require(endpoint["bin_bytes"] - light["bin_bytes"] == -1028, "endpoint-v0 BIN delta does not reconcile")
require(endpoint["text_section_bytes"] - light["text_section_bytes"] == -980, "endpoint-v0 text delta does not reconcile")

er = m["endpoint_v0_reproduction"]
require(er.get("source") == "official_vendor_template", "endpoint-v0 reproduction must start at official template")
require(er.get("seed_generation") == "slc_new_project", "endpoint-v0 independent seed must use SLC new-project")
require(set(er.get("remove_components", [])) == {"simple_led", "simple_button"}, "endpoint-v0 board-only exclusions must remain explicit")
require(er.get("configuration") == {"SL_ZIGBEE_NEIGHBOR_TABLE_SIZE": 26}, "endpoint-v0 router override drift")
require(er.get("seed_overlay_tools") == ["tools/apply_silabs_light_core.py", "tools/apply_silabs_endpoint_profile.py"], "endpoint-v0 overlay chain drift")
require(er.get("endpoint_validator") == "tools/verify_endpoint_profile.py", "endpoint-v0 validator drift")
require(er.get("independent_clean_build_success") is True and er.get("independent_byte_equal") is True, "endpoint-v0 deterministic rebuild not proven")

require(endpoint_profile.get("endpoint_id") == 1, "endpoint profile file endpoint drift")
require(endpoint_profile.get("profile_id") == 0x0104, "endpoint profile file HA profile drift")
require(endpoint_profile.get("device_type") == 0x010D, "endpoint profile file device type drift")
require(endpoint_profile.get("server_clusters") == endpoint.get("server_clusters"), "endpoint profile/server build evidence mismatch")
require(endpoint_profile.get("client_clusters") == endpoint.get("client_clusters"), "endpoint profile/client build evidence mismatch")
require(endpoint_profile.get("manufacturer_name") == endpoint.get("basic_manufacturer_name"), "endpoint profile manufacturer/build mismatch")
require(endpoint_profile.get("model_id") == endpoint.get("basic_model_id"), "endpoint profile model/build mismatch")
require(endpoint_profile.get("zcl_manufacturer_code") == 0x100B, "endpoint profile manufacturer-code metadata drift")
require(endpoint_profile.get("ota_identity_runtime_pending") is True, "endpoint profile OTA identity must remain pending")
require(endpoint_profile.get("physical_output_implementation") == "weak_noop", "endpoint profile physical output must remain no-op")
require(endpoint_profile.get("deployment_eligible") is False, "endpoint profile must remain non-deployable")
endpoint_tool_text = ENDPOINT_TOOL.read_text(encoding="utf-8")
require("validate_profile" in endpoint_tool_text and "_set_basic_identity" in endpoint_tool_text, "endpoint transformer safety validation missing")
endpoint_verify_text = ENDPOINT_VERIFY.read_text(encoding="utf-8")
require("deployment=false" in endpoint_verify_text, "endpoint verifier must report non-deployment state")
light_core_text = LIGHT_CORE.read_text(encoding="utf-8")
require("output->level = state->level;" in light_core_text, "renderer must preserve exact ZCL level")
require("state->on && state->level == 0u" not in light_core_text, "logical core must not apply hidden zero-level floor")
require("output->enabled == state->on" in light_core_text, "consistency check must compare On/Off exactly")
require("output->level == state->level" in light_core_text, "consistency check must compare level exactly")
adapter_text = ADAPTER.read_text(encoding="utf-8")
require("__attribute__((weak)) void hb_board_apply_output" in adapter_text, "board output hook must remain weak")
require("(void)output;" in adapter_text, "weak board output hook must remain a no-op")

custom_text = "\n".join(path.read_text(encoding="utf-8") for path in APP_DIR.glob("hallbulb_*.[ch]"))
for token in (r"\bGPIO\b", r"\bPWM\b", r"\bPA3\b", r"\bPD2\b", r"\bPC5\b", r"\bPA4\b", r"\bPA0\b"):
    require(re.search(token, custom_text, re.IGNORECASE) is None, f"board-neutral sources contain forbidden hardware token {token}")
overlay_text = OVERLAY_TOOL.read_text(encoding="utf-8")
require("patch_seed" in overlay_text and "stage_generated" in overlay_text, "overlay tool must support seed and generated stages")
require("hallbulb_light_state.c" in overlay_text and "hallbulb_zcl_adapter.c" in overlay_text, "overlay tool source set incomplete")

c = m["compatibility"]
require(c.get("live_ota_identity") == "0x100B/0x020C", "live OTA identity drift")
require(c.get("live_file_version") == "0x10003607", "live file-version baseline drift")
require(c.get("binary_bootloader_compatibility") == "UNRESOLVED_IDENTITY_MISMATCH", "compatibility must remain unresolved")
require(c.get("ota_container_produced") is False, "no OTA container should exist at this stage")
require(c.get("rollback_status") == "UNRESOLVED", "rollback must remain unresolved")
require(c.get("deployment_ready") is False, "structural/lightcore build must not be deployable")

require(tuya_reference.get("status") == "PENDING_TUYAOS_LIGHTING_FRAMEWORK", "Tuya reference must remain pending its lighting framework")
tr = tuya_reference.get("live_compatibility", {})
require(tr.get("live_tuple_checked") is True, "Tuya reference must record completed live tuple check")
require(tr.get("identity_match") is False, "generic Tuya reference identity must remain mismatched")
require(tr.get("deployable") is False, "generic Tuya reference build must remain non-deployable")
if errors:
    print("Silicon Labs router/lightcore build manifest validation FAILED:")
    for error in errors:
        print(f" - {error}")
    sys.exit(1)

print("Silicon Labs router/lightcore/endpoint build manifest validation PASS")
print(f" router_v0={rtr['bin_sha256'][:12]}... lightcore={light['bin_sha256'][:12]}... endpoint={endpoint['bin_sha256'][:12]}...")
print(" neighbor 16->26; endpoint 1=0x0104/0x010D; exact Basic identity; deployment=false")
