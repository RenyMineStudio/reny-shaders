#version 120

/*
 * Reny Shaders — Final Pass Fragment Shader
 * Composites scene and renders capability probe visual feedback
 */

#include "/lib/common.glsl"
#include "/lib/probe_hud.glsl"

uniform sampler2D colortex0; // Scene color
uniform sampler2D colortex1; // Normal / depth data
uniform sampler2D colortex2; // Encoded material ID / RGBA16F format
uniform sampler2D colortex3; // Persistent history buffer
uniform sampler2D colortex4; // Deferred signature / R11F_G11F_B10F format
uniform sampler2D depthtex0; // Depth buffer

// Core uniforms to test
uniform int frameCounter;
uniform float frameTime;
uniform float frameTimeCounter;
uniform int worldTime;
uniform vec3 sunPosition;
uniform vec3 cameraPosition;
uniform vec3 previousCameraPosition;

varying vec2 texcoord;

void main() {
    vec4 sceneColor = texture2D(colortex0, texcoord);
    vec4 finalColor = sceneColor;

    #if PROBE_MODE == PROBE_MODE_BASELINE
        // ---------------------------------------------------------------------
        // Mode 0: Clean Pass-Through Baseline
        // ---------------------------------------------------------------------
        // Preserves vanilla colors, lighting, and textures cleanly.
        // Adds only a small discrete mode indicator badge in the corner.
        finalColor = renderModeBadge(texcoord, PROBE_MODE_BASELINE, sceneColor);

    #elif PROBE_MODE == PROBE_MODE_CAPABILITY
        // ---------------------------------------------------------------------
        // Mode 1: Uniform & Capability Verification
        // ---------------------------------------------------------------------
        // Visualizes live uniforms: frameCounter heartbeat, frameTime bar,
        // sun altitude indicator, and world time tracker.
        finalColor = renderCapabilityHUD(
            texcoord,
            frameCounter,
            frameTime,
            sunPosition,
            worldTime,
            sceneColor
        );
        finalColor = renderModeBadge(texcoord, PROBE_MODE_CAPABILITY, finalColor);

    #elif PROBE_MODE == PROBE_MODE_HISTORY
        // ---------------------------------------------------------------------
        // Mode 2: Skip-Clear & History Persistence Probe
        // ---------------------------------------------------------------------
        // Blends the persistent history buffer (colortex3) onto the scene.
        // A visible trailing arc proves skip-clear persistence across frames.
        vec4 historyVal = texture2D(colortex3, texcoord);
        
        // Blend persistent history marker trail brightly onto scene
        finalColor.rgb = mix(sceneColor.rgb * 0.5, historyVal.rgb * 2.0, historyVal.a);
        finalColor = renderModeBadge(texcoord, PROBE_MODE_HISTORY, finalColor);

    #elif PROBE_MODE == PROBE_MODE_MATERIAL
        // ---------------------------------------------------------------------
        // Mode 3: Material ID & Block Mapping Probe
        // ---------------------------------------------------------------------
        // Visualizes block mapping from block.properties / mc_Entity.x.
        vec4 matSample = texture2D(colortex2, texcoord);
        float rawId = matSample.r * 255.0;
        float hasMappedId = matSample.b;

        if (hasMappedId > 0.5) {
            vec3 semanticColor = idToColor(rawId);
            // Blend 70% semantic false-color with 30% original scene texture
            finalColor.rgb = mix(sceneColor.rgb, semanticColor, 0.70);
        } else {
            // Unmapped or background: slightly desaturated scene color
            float luma = dot(sceneColor.rgb, vec3(0.299, 0.587, 0.114));
            finalColor.rgb = mix(sceneColor.rgb, vec3(luma), 0.35);
        }
        finalColor = renderModeBadge(texcoord, PROBE_MODE_MATERIAL, finalColor);

    #elif PROBE_MODE == PROBE_MODE_FORMATS
        // ---------------------------------------------------------------------
        // Mode 4: Buffer Formats Probe (RGBA16F, R11F_G11F_B10F, RGBA32F)
        // ---------------------------------------------------------------------
        // Splits the screen to verify reading and rendering from wide formats.
        if (texcoord.x < 0.5) {
            // Left half: colortex2 (RGBA16F format)
            vec4 fp16Sample = texture2D(colortex2, texcoord);
            finalColor.rgb = fp16Sample.rgb;
        } else {
            // Right half: colortex4 (R11F_G11F_B10F format)
            vec4 r11fSample = texture2D(colortex4, texcoord);
            finalColor.rgb = r11fSample.rgb;
        }
        finalColor = renderModeBadge(texcoord, PROBE_MODE_FORMATS, finalColor);

    #elif PROBE_MODE == PROBE_MODE_DEFERRED
        // ---------------------------------------------------------------------
        // Mode 5: Deferred Pass Validation Probe
        // ---------------------------------------------------------------------
        // Inspects whether deferred.fsh executed and wrote its magic signature.
        vec4 defSample = texture2D(colortex4, texcoord);
        bool defPassed = (defSample.a > 0.5) && (distance(defSample.rgb, RENY_DEFERRED_MAGIC.rgb) < 0.08);

        // Top banner: green if deferred executed, red if failed
        if (inBox(texcoord, vec2(0.25, 0.88), vec2(0.75, 0.94))) {
            finalColor = defPassed ? vec4(0.1, 0.9, 0.2, 1.0) : vec4(0.9, 0.1, 0.1, 1.0);
        } else {
            finalColor = sceneColor;
        }
        finalColor = renderModeBadge(texcoord, PROBE_MODE_DEFERRED, finalColor);

    #else
        finalColor = sceneColor;
    #endif

    gl_FragColor = finalColor;
}
