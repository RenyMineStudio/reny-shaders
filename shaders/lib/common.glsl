#ifndef RENY_COMMON_GLSL
#define RENY_COMMON_GLSL

/*
 * Reny Shaders — Common definitions and uniforms
 * OptiFine 1.7.10 HD U E7 legacy pipeline
 */

#include "/lib/probe_config.glsl"

// Math helper functions
float saturate(float x) {
    return clamp(x, 0.0, 1.0);
}

vec2 saturate(vec2 x) {
    return clamp(x, vec2(0.0), vec2(1.0));
}

vec3 saturate(vec3 x) {
    return clamp(x, vec3(0.0), vec3(1.0));
}

vec4 saturate(vec4 x) {
    return clamp(x, vec4(0.0), vec4(1.0));
}

// Convert block ID to a distinctive semantic pseudo-color for visualization
vec3 idToColor(float id) {
    if (id < 0.5) return vec3(0.1, 0.1, 0.1);      // Unmapped / Default
    if (id < 100.5) return vec3(0.3, 0.3, 0.3);    // Vanilla standard block
    if (id < 101.5) return vec3(0.4, 0.25, 0.1);   // Dirt / Grass (ID 100)
    if (id < 102.5) return vec3(0.5, 0.35, 0.2);   // Wood / Logs (ID 101)
    if (id < 103.5) return vec3(0.1, 0.7, 0.2);    // Leaves / Foliage (ID 102)
    if (id < 104.5) return vec3(0.1, 0.4, 0.9);    // Water (ID 103)
    if (id < 105.5) return vec3(1.0, 0.4, 0.0);    // Lava (ID 104)
    if (id < 106.5) return vec3(0.9, 0.8, 0.2);    // Ores (ID 105)
    if (id < 107.5) return vec3(1.0, 0.9, 0.5);    // Torch / Emissive (ID 106)
    if (id < 108.5) return vec3(0.6, 0.1, 0.9);    // Portal (ID 107)
    if (id < 109.5) return vec3(0.9, 0.9, 0.9);    // Cobweb (ID 108)
    if (id < 120.5) return vec3(0.8, 0.2, 0.7);    // Modded Ore / Wood (ID 120)
    if (id < 121.5) return vec3(0.3, 0.9, 0.4);    // Modded Foliage (ID 121)
    if (id < 122.5) return vec3(0.9, 0.5, 0.2);    // Modded Metal (ID 122)
    
    // Hash fallback for any higher ID
    float r = fract(sin(id * 12.9898) * 43758.5453);
    float g = fract(sin((id + 1.0) * 78.233) * 43758.5453);
    float b = fract(sin((id + 2.0) * 45.164) * 43758.5453);
    return vec3(r, g, b);
}

#endif // RENY_COMMON_GLSL
