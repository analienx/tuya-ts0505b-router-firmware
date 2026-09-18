#ifndef HALLBULB_ZCL_ADAPTER_H
#define HALLBULB_ZCL_ADAPTER_H

#include <stdint.h>

#include "hallbulb_light_state.h"

void hb_zcl_sync_output(uint8_t endpoint);
void hb_board_apply_output(const hb_light_output_t *output);

#endif
