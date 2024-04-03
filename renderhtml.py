import base64
import io
from PIL import Image
from urllib.parse import quote

def color_array_html_render(color_array):
    color_html = ""
    for color in color_array:
        hex_color = f"#{color[1][0]:02X}{color[1][1]:02X}{color[1][2]:02X}"
        r, g, b = color[1]
        # Calculate the YIQ contrast
        yiq = ((r * 299) + (g * 587) + (b * 114)) / 1000
        # Choose black (#000000) for bright colors, and white (#ffffff) for dark colors
        inverse_color = '#000000' if yiq >= 128 else '#FFFFFF'
        color_html += f'''<div style="background-color: {hex_color}; color: {inverse_color}" class="colorswatch" onclick="copyToClipboardAndPulse(this, '{hex_color}')">
            {hex_color}
        </div>'''
    return color_html

def render_html_block(text:str, encoded_image:str, image:Image):
    encoded_text = quote(text)
    return (
        f'<details>'
        f'<summary>{text.upper()}</summary>'
        f'<img src="data:image/png;base64,{encoded_image}"/>'
        f'<div style="text-align:center"><a href="/cachedimages/{encoded_text}" class="permalink">PERMALINK AND DETAILS</a><br>CLICKABLE COLOR PALETTE</div>'
        f'<br>{color_array_html_render(image.convert("RGB").getcolors(maxcolors=16))}'
        f'</details>'
    )

def render_main_display(messages: list, cudawarning: bool = False):
    cuda_warning_message = "<br><p class=\"cudawarning\">Warning: CUDA is not available. Pixel Inspiration has defaulted to CPU. Image generation may take half an hour or more.</p>" if cudawarning else ""
    return f'''
        {get_head()}
        <body>
        <h1>PIXEL INSPIRATIONS</h1>
            <div class="pastmessages">
                {"<br>".join(messages)}
            </div>
            <div id="loader" style="display: none;">
                <img src="/static/pixel-walk-load-icon.gif" alt="Loading..."/>
                <br>
                <p class="loadingPopup">I'm on my way to get you your image!{cuda_warning_message}</p>
            </div>
            <form id="myForm" method="POST" action="/">
                <input type="text" id="myTextInput" name="text" maxlength="500"/>
            </form>
        </body>
    '''

def get_head():
    with open('head.html', 'r') as file:
        return file.read()
    

def render_specific_image_html(image_record):
    image_raw = Image.open(io.BytesIO(image_record.image))
    byte_arr = io.BytesIO()
    image_raw.save(byte_arr, format='PNG')
    encoded_image = base64.encodebytes(byte_arr.getvalue()).decode('ascii')

    # Full pixel image
    full_pixel_image = process_img_to_full_pixel(image_raw.copy())
    byte_arr_full = io.BytesIO()
    full_pixel_image.save(byte_arr_full, format='PNG')
    encoded_image_full = base64.encodebytes(byte_arr_full.getvalue()).decode('ascii')

    # Small pixel image
    small_pixel_image = process_img_to_small_pixel(image_raw.copy())
    byte_arr_small = io.BytesIO()
    small_pixel_image.save(byte_arr_small, format='PNG')
    encoded_image_small = base64.encodebytes(byte_arr_small.getvalue()).decode('ascii')

    return f'''
        {get_head()}
        <body>
            <h1>{image_record.text.upper()}</h1>
            SOURCE IMAGE AND ITS PSEUDO-PIXEL-ART VERSION.
            <div style="display: flex; justify-content: space-between;">
                <img src="data:image/png;base64,{encoded_image}"/>
                <img src="data:image/png;base64,{encoded_image_full}"/>
            </div><br><br>
            <div class="colordisplay">{color_array_html_render(small_pixel_image.convert("RGB").getcolors(maxcolors=16))}</div>
            <img style="margin: 0px" src="data:image/png;base64,{encoded_image_small}"/><br><div style="font-size:9px">SMALL PIXEL IMAGE FOR COPYPASTING!</div>
        </body>'''



def process_img_to_full_pixel(image):
    return process_img_to_small_pixel(image).resize((512, 512))

def process_img_to_small_pixel(image):
    return image.convert("P", palette=Image.ADAPTIVE, colors=16).resize((128, 128))