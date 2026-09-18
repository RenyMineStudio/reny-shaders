#version 120

/* DRAWBUFFERS:0 */

uniform sampler2D texture;
uniform sampler2D lightmap;

varying vec4 color;
varying vec2 texcoord;
varying vec2 lmcoord;

void main() {
    vec4 texColor = texture2D(texture, texcoord) * color;
    if (texColor.a < 0.05) discard;
    vec4 light = texture2D(lightmap, lmcoord);
    gl_FragData[0] = texColor * light;
}
