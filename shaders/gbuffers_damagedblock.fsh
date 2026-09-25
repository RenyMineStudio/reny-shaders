#version 120

/* DRAWBUFFERS:0 */

uniform sampler2D texture;

varying vec4 color;
varying vec2 texcoord;

void main() {
    vec4 texColor = texture2D(texture, texcoord) * color;
    if (texColor.a < 0.1) discard;
    gl_FragData[0] = texColor;
}
