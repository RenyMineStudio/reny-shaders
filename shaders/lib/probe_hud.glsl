#ifndef RENY_PROBE_HUD_GLSL
#define RENY_PROBE_HUD_GLSL

/*
 * Reny Shaders — On-screen Capability Probe HUD / Diagnostic Patterns
 * Conservative GLSL 1.20 compatible
 */

#include "/lib/common.glsl"

// Helper to draw an axis-aligned box on normalized screen coordinates [0, 1]
bool inBox(vec2 coord, vec2 minPos, vec2 maxPos) {
    return coord.x >= minPos.x && coord.x <= maxPos.x &&
           coord.y >= minPos.y && coord.y <= maxPos.y;
}

// Compute the dynamic position of the moving test marker for history validation
vec2 getHistoryProbePos(int frame, float timeSec) {
    // Moves across screen in a repeating Lissajous or orbital path
    float angle = timeSec * 1.5;
    float x = 0.5 + 0.35 * cos(angle);
    float y = 0.5 + 0.35 * sin(angle * 1.3);
    return vec2(x, y);
}

// Render mode badge indicator in top-left corner
vec4 renderModeBadge(vec2 uv, int mode, vec4 baseColor) {
    // Badge area: x in [0.02, 0.16], y in [0.92, 0.98]
    if (inBox(uv, vec2(0.02, 0.92), vec2(0.16, 0.98))) {
        // Border
        if (uv.x < 0.023 || uv.x > 0.157 || uv.y < 0.926 || uv.y > 0.974) {
            return vec4(1.0, 1.0, 1.0, 1.0);
        }
        // Background color encodes active mode
        if (mode == PROBE_MODE_BASELINE)   return vec4(0.1, 0.4, 0.1, 0.9); // Green = baseline
        if (mode == PROBE_MODE_CAPABILITY) return vec4(0.1, 0.2, 0.7, 0.9); // Blue = capability
        if (mode == PROBE_MODE_HISTORY)    return vec4(0.8, 0.4, 0.0, 0.9); // Orange = history
        if (mode == PROBE_MODE_MATERIAL)   return vec4(0.7, 0.1, 0.6, 0.9); // Magenta = material
        if (mode == PROBE_MODE_FORMATS)    return vec4(0.0, 0.6, 0.7, 0.9); // Cyan = formats
        if (mode == PROBE_MODE_DEFERRED)   return vec4(0.7, 0.7, 0.0, 0.9); // Yellow = deferred
    }
    return baseColor;
}

// Diagnostic HUD for capability verification (Mode 1)
vec4 renderCapabilityHUD(
    vec2 uv,
    int frame,
    float frameTimeSec,
    vec3 sunPos,
    int timeTicks,
    vec4 baseColor
) {
    // 1. Frame counter heartbeat indicator (box at [0.02, 0.85] to [0.06, 0.90])
    if (inBox(uv, vec2(0.02, 0.85), vec2(0.06, 0.90))) {
        // Toggle color every 30 frames using GLSL 1.20 compatible float mod
        bool pulse = mod(floor(float(frame) / 30.0), 2.0) < 1.0;
        return pulse ? vec4(0.0, 1.0, 0.2, 1.0) : vec4(0.0, 0.2, 0.0, 1.0);
    }

    // 2. Frame time indicator bar (box at [0.07, 0.85] to [0.25, 0.90])
    if (inBox(uv, vec2(0.07, 0.85), vec2(0.25, 0.90))) {
        // Expected frame time between 0ms and 50ms (0.05s)
        float normalizedFT = clamp(frameTimeSec / 0.05, 0.0, 1.0);
        float barX = (uv.x - 0.07) / 0.18;
        if (barX <= normalizedFT) {
            vec3 barColor = mix(vec3(0.0, 1.0, 0.0), vec3(1.0, 0.0, 0.0), normalizedFT);
            return vec4(barColor, 1.0);
        }
        return vec4(0.05, 0.05, 0.05, 0.8);
    }

    // 3. Sun altitude indicator (box at [0.02, 0.78] to [0.06, 0.83])
    if (inBox(uv, vec2(0.02, 0.78), vec2(0.06, 0.83))) {
        // Green if sun above horizon, red if below
        bool sunUp = sunPos.y > 0.0;
        return sunUp ? vec4(1.0, 0.9, 0.1, 1.0) : vec4(0.1, 0.1, 0.4, 1.0);
    }

    // 4. World time tick progression (box at [0.07, 0.78] to [0.25, 0.83])
    if (inBox(uv, vec2(0.07, 0.78), vec2(0.25, 0.83))) {
        float dayFraction = mod(float(timeTicks), 24000.0) / 24000.0;
        float barX = (uv.x - 0.07) / 0.18;
        if (barX <= dayFraction) {
            return vec4(0.2, 0.6, 1.0, 1.0);
        }
        return vec4(0.05, 0.05, 0.05, 0.8);
    }

    return baseColor;
}

#endif // RENY_PROBE_HUD_GLSL
