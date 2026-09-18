import tempfile
import unittest
from pathlib import Path

from tools.apply_silabs_light_core import FILES, patch_seed, stage_generated


MIN_APP = '''#include "app/framework/include/af.h"
void sl_zigbee_af_post_attribute_change_cb(void) {
  uint8_t endpoint = 1;
  uint16_t clusterId = 0;
  uint8_t mask = CLUSTER_MASK_SERVER;
  const uint8_t *value = 0;
  (void)value;
}
'''

MIN_SLCP = '''project_name: test
source:
- path: app.c
'''


class SilabsLightcoreOverlayTests(unittest.TestCase):
    def test_seed_patch_is_idempotent(self):
        with tempfile.TemporaryDirectory() as td:
            project = Path(td)
            slcp = project / "test.slcp"
            slcp.write_text(MIN_SLCP, encoding="utf-8")
            (project / "app.c").write_text(MIN_APP, encoding="utf-8")
            patch_seed(project, slcp)
            patch_seed(project, slcp)

            text = slcp.read_text(encoding="utf-8")
            self.assertEqual(text.count("- path: hallbulb_light_state.c"), 1)
            self.assertEqual(text.count("- path: hallbulb_zcl_adapter.c"), 1)
            app = (project / "app.c").read_text(encoding="utf-8")
            self.assertEqual(app.count('#include "hallbulb_zcl_adapter.h"'), 1)
            self.assertEqual(app.count("hb_zcl_sync_output(endpoint);"), 1)
            for name in FILES:
                self.assertTrue((project / name).is_file(), name)

    def test_generated_stage_is_idempotent(self):
        with tempfile.TemporaryDirectory() as td:
            project = Path(td)
            app = MIN_APP.replace(
                '#include "app/framework/include/af.h"\n',
                '#include "app/framework/include/af.h"\n#include "hallbulb_zcl_adapter.h"\n',
            ).replace(
                "  (void)value;\n",
                "  (void)value;\n  hb_zcl_sync_output(endpoint);\n",
            )
            (project / "app.c").write_text(app, encoding="utf-8")
            stage_generated(project)
            stage_generated(project)
            for name in FILES:
                self.assertTrue((project / name).is_file(), name)


if __name__ == "__main__":
    unittest.main()
