#ifndef HALLBULB_LIGHT_STATE_H
#define HALLBULB_LIGHT_STATE_H

#include <stdbool.h>
#include <stdint.h>

typedef enum {
  HB_COLOR_MODE_CT = 0,
  HB_COLOR_MODE_HS = 1,
  HB_COLOR_MODE_XY = 2,
} hb_color_mode_t;

typedef struct {
  bool on;
  uint8_t level;
  hb_color_mode_t mode;
  uint16_t color_temperature_mired;
  uint8_t hue;
  uint8_t saturation;
  uint16_t x;
  uint16_t y;
} hb_light_state_t;
typedef struct {
  bool enabled;
  uint8_t level;
  hb_color_mode_t mode;
  uint16_t color_temperature_mired;
  uint8_t hue;
  uint8_t saturation;
  uint16_t x;
  uint16_t y;
} hb_light_output_t;

void hb_light_state_init(hb_light_state_t *state);
void hb_light_apply_on_off(hb_light_state_t *state, bool on);
void hb_light_apply_level(hb_light_state_t *state, uint8_t level, bool with_on_off);
void hb_light_apply_color_temperature(hb_light_state_t *state, uint16_t mired);
void hb_light_apply_hs(hb_light_state_t *state, uint8_t hue, uint8_t saturation);
void hb_light_apply_xy(hb_light_state_t *state, uint16_t x, uint16_t y);
void hb_light_render(const hb_light_state_t *state, hb_light_output_t *output);
bool hb_light_state_is_consistent(const hb_light_state_t *state, const hb_light_output_t *output);

#endif
