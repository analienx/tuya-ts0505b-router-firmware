import crypto from "node:crypto";
import fs from "node:fs";
import path from "node:path";

const PATCH = Symbol.for("ts0505b.d0.validationHold");
const STATUS_TOPIC = "bridge/d0_validation_hold";
const LAUNCH_STATUS_TOPIC = "bridge/d0_validation_hold_launch";
const MANUFACTURER = 0x100b;
const IMAGE_TYPE = 0x020c;
const FILE_VERSION = 0x10003608;
const HOLD_TIME = 0xffffffff;
const ONE_SHOT_PACKAGE_NAME = "HallBulb2-d0-validation-hold-AUTHORIZED.json";
const ONE_SHOT_SENTINEL_NAME = "HallBulb2-d0-validation-hold-FIRED.json";
const AUTHORIZATION_SCOPE = "one HallBulb2 validation-hold OTA transfer; no application activation";

const FROZEN_EXPECTED = Object.freeze({
    target: "HallBulb2",
    topic: "zigbee2mqtt/bridge/request/device/ota_update/update",
    otaSha256: "55d976078d573aa4dd8833d8af0f000aacbdbef9850bb1e65e1ffe8c4816c549",
    otaSize: 304602,
    manufacturerCode: MANUFACTURER,
    imageType: IMAGE_TYPE,
    fileVersion: FILE_VERSION,
    fileName: "hallbulb-d0.1-noled.ota",
});

function matchesFrozenD0(clusterKey, commandKey, payload) {
    const otaCluster = clusterKey === "genOta" || clusterKey === 0x0019;
    const upgradeEnd = commandKey === "upgradeEndResponse" || commandKey === 0x07;

    return (
        otaCluster &&
        upgradeEnd &&
        payload?.manufacturerCode === MANUFACTURER &&
        payload?.imageType === IMAGE_TYPE &&
        payload?.fileVersion === FILE_VERSION
    );
}
function validateAuthorizedPackage(pkg, expected = FROZEN_EXPECTED) {
    if (pkg?.mutation_authorized !== true) {
        throw new Error("authorized package flag is not true");
    }
    if (pkg?.authorization_scope !== AUTHORIZATION_SCOPE) {
        throw new Error("authorization scope mismatch");
    }
    if (pkg?.topic !== expected.topic) {
        throw new Error("OTA request topic mismatch");
    }
    if (pkg?.payload?.id !== expected.target) {
        throw new Error("OTA target mismatch");
    }
    if (pkg?.payload?.hex?.file_name !== expected.fileName) {
        throw new Error("OTA filename mismatch");
    }
    if (pkg?.guard?.validation_hold_required !== true) {
        throw new Error("validation-hold guard not required by package");
    }
    if (
        pkg?.guard?.manufacturer_code !== expected.manufacturerCode ||
        pkg?.guard?.image_type !== expected.imageType ||
        pkg?.guard?.file_version !== expected.fileVersion ||
        pkg?.guard?.ota_sha256 !== expected.otaSha256
    ) {
        throw new Error("frozen OTA guard mismatch");
    }

    const hex = pkg?.payload?.hex?.data;
    if (typeof hex !== "string" || hex.length !== expected.otaSize * 2 || !/^[0-9a-f]+$/i.test(hex)) {
        throw new Error("OTA hex payload length/encoding mismatch");
    }
    const image = Buffer.from(hex, "hex");
    if (image.length !== expected.otaSize || image.toString("hex").length !== hex.length) {
        throw new Error("OTA decoded size mismatch");
    }
    const digest = crypto.createHash("sha256").update(image).digest("hex");
    if (digest !== expected.otaSha256) {
        throw new Error("OTA SHA-256 mismatch");
    }
    if (
        image.readUInt32LE(0) !== 0x0beef11e ||
        image.readUInt16LE(10) !== expected.manufacturerCode ||
        image.readUInt16LE(12) !== expected.imageType ||
        image.readUInt32LE(14) !== expected.fileVersion ||
        image.readUInt32LE(52) !== expected.otaSize
    ) {
        throw new Error("OTA header mismatch");
    }

    return {image, digest};
}
export default class D0ValidationHold {
    constructor(zigbee, mqtt, _state, _publishEntityState, _eventBus, _enableDisableExtension, _restartCallback, _addExtension, _settings, logger) {
        this.zigbee = zigbee;
        this.mqtt = mqtt;
        this.logger = logger;
        this.endpointPrototype = undefined;
        this.wrapper = undefined;
        this.expected = FROZEN_EXPECTED;
        this.oneShotDir = process.env.Z2M_D0_ONESHOT_DIR || "/config/zigbee2mqtt/d0_once";
    }

    async start() {
        const controller = this.zigbee?.zhController;
        if (!controller || typeof controller.getDevicesIterator !== "function") {
            throw new Error("D0 validation hold: zigbee-herdsman controller API unavailable");
        }

        let endpoint;
        for (const device of controller.getDevicesIterator()) {
            if (device?.endpoints?.length) {
                endpoint = device.endpoints[0];
                break;
            }
        }

        if (!endpoint) {
            throw new Error("D0 validation hold: no endpoint available to establish commandResponse hook");
        }

        const prototype = Object.getPrototypeOf(endpoint);
        const original = prototype?.commandResponse;
        if (!prototype || typeof original !== "function") {
            throw new Error("D0 validation hold: endpoint commandResponse API unavailable");
        }
        if (prototype[PATCH]) {
            throw new Error("D0 validation hold: commandResponse hook is already installed");
        }

        const logger = this.logger;
        const wrapper = async function (clusterKey, commandKey, payload, options, transactionSequenceNumber) {
            if (matchesFrozenD0(clusterKey, commandKey, payload)) {
                if (payload.currentTime !== 0 || payload.upgradeTime !== 1) {
                    throw new Error(
                        `D0 validation hold: refusing unexpected Upgrade End timing currentTime=${payload.currentTime} upgradeTime=${payload.upgradeTime}`,
                    );
                }

                const held = {...payload, upgradeTime: HOLD_TIME};
                logger?.warning?.(
                    `D0 validation hold: suppressing activation for ${this.deviceIeeeAddress ?? "unknown-device"}; upgradeTime=0xFFFFFFFF`,
                );
                return await Reflect.apply(original, this, [clusterKey, commandKey, held, options, transactionSequenceNumber]);
            }

            return await Reflect.apply(original, this, [clusterKey, commandKey, payload, options, transactionSequenceNumber]);
        };

        prototype[PATCH] = {original, wrapper};
        prototype.commandResponse = wrapper;
        this.endpointPrototype = prototype;
        this.wrapper = wrapper;

        await this.publishStatus(true);
        await this.maybeLaunchAuthorizedOneShot();
    }
    async maybeLaunchAuthorizedOneShot() {
        const packagePath = path.join(this.oneShotDir, ONE_SHOT_PACKAGE_NAME);
        const sentinelPath = path.join(this.oneShotDir, ONE_SHOT_SENTINEL_NAME);

        if (!fs.existsSync(packagePath)) {
            await this.publishLaunchStatus({state: "not-armed"});
            return;
        }
        if (fs.existsSync(sentinelPath)) {
            this.logger?.warning?.("D0 one-shot sentinel already exists; refusing replay");
            await this.publishLaunchStatus({state: "blocked-replay", sentinel: sentinelPath});
            return;
        }

        let pkg;
        try {
            pkg = JSON.parse(fs.readFileSync(packagePath, "utf8").replace(/^\uFEFF/, ""));
            validateAuthorizedPackage(pkg, this.expected);
        } catch (error) {
            this.logger?.error?.(`D0 one-shot validation failed: ${error.message}`);
            await this.publishLaunchStatus({state: "validation-failed", error: error.message});
            return;
        }

        fs.mkdirSync(this.oneShotDir, {recursive: true});
        const reserved = {
            state: "reserved",
            target: this.expected.target,
            ota_sha256: this.expected.otaSha256,
            reserved_at: new Date().toISOString(),
            authorization_scope: AUTHORIZATION_SCOPE,
        };
        try {
            fs.writeFileSync(sentinelPath, `${JSON.stringify(reserved, null, 2)}\n`, {encoding: "utf8", flag: "wx"});
        } catch (error) {
            this.logger?.error?.(`D0 one-shot sentinel reservation failed: ${error.message}`);
            await this.publishLaunchStatus({state: "reservation-failed", error: error.message});
            return;
        }

        await this.publishLaunchStatus({state: "reserved", target: this.expected.target, ota_sha256: this.expected.otaSha256});
        try {
            const relativeTopic = pkg.topic.startsWith("zigbee2mqtt/") ? pkg.topic.slice("zigbee2mqtt/".length) : pkg.topic;
            await this.mqtt.publish(relativeTopic, JSON.stringify(pkg.payload), {skipReceive: false});
            const published = {...reserved, state: "published", published_at: new Date().toISOString()};
            fs.writeFileSync(sentinelPath, `${JSON.stringify(published, null, 2)}\n`, "utf8");
            this.logger?.warning?.(`D0 one-shot published for ${this.expected.target}; replay sentinel is armed`);
            await this.publishLaunchStatus({state: "published", target: this.expected.target, ota_sha256: this.expected.otaSha256});
        } catch (error) {
            this.logger?.error?.(`D0 one-shot publish failed after reservation: ${error.message}`);
            await this.publishLaunchStatus({state: "publish-failed", error: error.message});
        }
    }
    async stop() {
        const prototype = this.endpointPrototype;
        const record = prototype?.[PATCH];
        if (prototype && record?.wrapper === this.wrapper && prototype.commandResponse === this.wrapper) {
            prototype.commandResponse = record.original;
            delete prototype[PATCH];
        }

        this.endpointPrototype = undefined;
        this.wrapper = undefined;
        await this.publishStatus(false);
    }

    async publishStatus(active) {
        const payload = JSON.stringify({
            active,
            mode: "validation-hold",
            manufacturerCode: "0x100B",
            imageType: "0x020C",
            fileVersion: "0x10003608",
            upgradeTime: active ? "0xFFFFFFFF" : null,
        });

        if (typeof this.mqtt?.publish === "function") {
            await this.mqtt.publish(STATUS_TOPIC, payload, {clientOptions: {retain: true}});
        }
    }

    async publishLaunchStatus(extra) {
        if (typeof this.mqtt?.publish !== "function") {
            return;
        }
        const payload = JSON.stringify({
            mode: "authorized-one-shot",
            manufacturerCode: "0x100B",
            imageType: "0x020C",
            fileVersion: "0x10003608",
            ...extra,
        });
        await this.mqtt.publish(LAUNCH_STATUS_TOPIC, payload, {clientOptions: {retain: true}});
    }
}

export {
    AUTHORIZATION_SCOPE,
    FILE_VERSION,
    FROZEN_EXPECTED,
    HOLD_TIME,
    IMAGE_TYPE,
    LAUNCH_STATUS_TOPIC,
    MANUFACTURER,
    STATUS_TOPIC,
    matchesFrozenD0,
    validateAuthorizedPackage,
};
