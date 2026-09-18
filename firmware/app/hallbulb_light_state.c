#include "hallbulb_light_state.h"

#include <stddef.h>

#define HB_DEFAULT_LEVEL 254u
#define HB_DEFAULT_CT_MIRED 370u
#define HB_CT_MIN_MIRED 153u
#define HB_CT_MAX_MIRED 500u

static uint16_t clamp_ct(uint16_t mired)
{
  if (mired < HB_CT_MIN_MIRED) {
    return HB_CT_MIN_MIRED;
  }
  if (mired > HB_CT_MAX_MIRED) {
    return HB_CT_MAX_MIRED;
  }
  return mired;
}

void hb_light_state_init(hb_light_state_t *state)
{
  if (state == NULL) {
    return;
  }
  state->on = false;
  state->level = HB_DEFAULT_LEVEL;
  state->mode = HB_COLOR_MODE_CT;
  state->color_temperature_mired = HB_DEFAULT_CT_MIRED;
  state->hue = 0u;
  state->saturation = 0u;
  state->x = 0u;
  state->y = 0u;
}

void hb_light_apply_on_off(hb_light_state_t *state, bool on)
{
  if (state == NULL) {
    return;
  }
  state->on = on;
}

void hb_light_apply_level(hb_light_state_t *state, uint8_t level, bool with_on_off)
{
  if (state == NULL) {
    return;
  }
  state->level = level;
  if (with_on_off) {
    state->on = (level != 0u);
  }
}
void hb_light_apply_color_temperature(hb_light_state_t *state, uint16_t mired)
{
  if (state == NULL) {
    return;
  }
  state->mode = HB_COLOR_MODE_CT;
  state->color_temperature_mired = clamp_ct(mired);
}

void hb_light_apply_hs(hb_light_state_t *state, uint8_t hue, uint8_t saturation)
{
  if (state == NULL) {
    return;
  }
  state->mode = HB_COLOR_MODE_HS;
  state->hue = hue;
  state->saturation = saturation;
}

void hb_light_apply_xy(hb_light_state_t *state, uint16_t x, uint16_t y)
{
  if (state == NULL) {
    return;
  }
  state->mode = HB_COLOR_MODE_XY;
  state->x = x;
  state->y = y;
}
void hb_light_render(const hb_light_state_t *state, hb_light_output_t *output)
{
  if (state == NULL || output == NULL) {
    return;
  }
  output->enabled = state->on;
  output->level = state->level;
  output->mode = state->mode;
  output->color_temperature_mired = state->color_temperature_mired;
  output->hue = state->hue;
  output->saturation = state->saturation;
  output->x = state->x;
  output->y = state->y;
}

bool hb_light_state_is_consistent(const hb_light_state_t *state, const hb_light_output_t *output)
{
  if (state == NULL || output == NULL) {
    return false;
  }
  return output->enabled == state->on
         && output->level == state->level
         && output->mode == state->mode
         && output->color_temperature_mired == state->color_temperature_mired
         && output->hue == state->hue
         && output->saturation == state->saturation
         && output->x == state->x
         && output->y == state->y;
}
