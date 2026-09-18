const PATCH = Symbol.for("ts0505b.d0.validationHold");
const STATUS_TOPIC = "bridge/d0_validation_hold";
const MANUFACTURER = 0x100b;
const IMAGE_TYPE = 0x020c;
const FILE_VERSION = 0x10003608;
const HOLD_TIME = 0xffffffff;

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

export default class D0ValidationHold {
    constructor(zigbee, mqtt, _state, _publishEntityState, _eventBus, _enableDisableExtension, _restartCallback, _addExtension, _settings, logger) {
        this.zigbee = zigbee;
        this.mqtt = mqtt;
        this.logger = logger;
        this.endpointPrototype = undefined;
        this.wrapper = undefined;
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
            await this.mqtt.publish(STATUS_TOPIC, payload, {retain: true});
        }
    }
}

export {FILE_VERSION, HOLD_TIME, IMAGE_TYPE, MANUFACTURER, STATUS_TOPIC, matchesFrozenD0};
