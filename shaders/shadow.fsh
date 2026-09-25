#version 120

/*
 * Reny Shaders — Shadow Pass Fragment Shader
 */

/* DRAWBUFFERS:0 */

uniform sampler2D tex;

varying vec2 texcoord;
varying vec4 color;

void main() {
    vec4 texColor = texture2D(tex, texcoord);
    if (texColor.a < 0.1) discard;
    gl_FragData[0] = texColor * color;
}
