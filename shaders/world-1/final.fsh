#version 120

/*
 * Reny Shaders — Nether Dimension (world-1) Final Pass
 * Demonstrates successful per-dimension world-folder selection in E7
 */

uniform sampler2D colortex0;

varying vec2 texcoord;

void main() {
    vec4 color = texture2D(colortex0, texcoord);

    // Dimension indicator badge (top-right corner: x in [0.84, 0.98], y in [0.92, 0.98])
    if (texcoord.x >= 0.84 && texcoord.x <= 0.98 && texcoord.y >= 0.92 && texcoord.y <= 0.98) {
        // Red / Nether border & background
        if (texcoord.x < 0.843 || texcoord.x > 0.977 || texcoord.y < 0.926 || texcoord.y > 0.974) {
            color = vec4(1.0, 0.2, 0.2, 1.0);
        } else {
            color = vec4(0.6, 0.05, 0.05, 0.95);
        }
    }

    gl_FragColor = color;
}
