import base64
import io
from PIL import Image
from urllib.parse import quote

def render_html_block(text:str, encoded_image:str, image:Image, dbexists:bool):
    # Every image must become an HTML block.
    encoded_text = quote(text)
    permalink = f'<a href="/cachedimages/{encoded_text}" class="permalink">PERMALINK AND DETAILS</a>' if dbexists else ""
    return (
        f'<details>'
        f'<summary>{text.upper()}</summary>'
        f'<img src="data:image/png;base64,{encoded_image}"/>'
        f'<div style="text-align:center">{permalink}<br><br>CLICKABLE COLOR PALETTE</div>'
        f'{color_array_html_render(image.convert("RGB").getcolors(maxcolors=16))}'
        f'</details>'
    )

def render_main_display(messages: list, cudawarning: bool = False):
    # Main page. Mostly static, but it joins in the messages from the AI, in their processed form.
    cuda_warning_message = "<br><p class=\"cudawarning\">Warning: CUDA is not available. Pixel Inspiration has defaulted to CPU. Image generation may take half an hour or more.</p>" if cudawarning else ""
    return f'''
        {get_head()}
        <body>
        <h1>PIXEL INSPIRATION</h1>
            <div class="pastmessages">
                {"<br>".join(messages)}
            </div>
            <div id="loader" style="display: none;">
                <img src="/static/pixel-walk-load-icon.gif" alt="Loading..."/> <!--I made this pixel art myself!-->
                <br>
                <p class="loadingPopup">I'm on my way to get you your image!{cuda_warning_message}</p>
            </div>
            <form id="myform" method="POST" action="/">
                <input type="text" id="mytextinput" name="text" maxlength="500"/>
            </form>
        </body>
    '''

def get_head():
    with open('head.html', 'r') as file:
        return file.read()

def color_array_html_render(color_array): 
    # I want to be able to quickly see and retrieve the color palette
    color_html = ""
    for color in color_array:
        # Let's get the hex color. I could get CMYKs and such instead, but this format is more consistently useable in art programs, I've found.
        hex_color = f"#{color[1][0]:02X}{color[1][1]:02X}{color[1][2]:02X}" 
        r, g, b = color[1]
        # Calculate the YIQ contrast. I'll admit: I know very little about this.
        # I did some frontend accessibility work ages ago and this is just one of those magic equations.
        yiq = ((r * 299) + (g * 587) + (b * 114)) / 1000
        # Choose black (#000000) for bright colors, and white (#ffffff) for dark colors
        inverse_color = '#000000' if yiq >= 128 else '#FFFFFF'
        color_html += f'''<div style="background-color: {hex_color}; color: {inverse_color}" class="colorswatch" onclick="copyToClipboardAndPulse(this, '{hex_color}')">
            {hex_color}
        </div>'''
        # You can click on it to copy it onto your clipboard. It's also got a little user feedback! See head.html for more.
    return color_html

def render_specific_image_html(image_record): # This is the permalink page. It's a little more detailed.
    image_raw = Image.open(io.BytesIO(image_record.image)) # It'll provide the source, raw image as well. Is that useful? Sometimes.
    byte_arr = io.BytesIO()
    image_raw.save(byte_arr, format='PNG')
    encoded_image = base64.encodebytes(byte_arr.getvalue()).decode('ascii')

    # Full pixel image
    full_pixel_image = process_img_to_full_pixel(image_raw.copy()) # The image as seen in the front page.
    byte_arr_full = io.BytesIO()
    full_pixel_image.save(byte_arr_full, format='PNG')
    encoded_image_full = base64.encodebytes(byte_arr_full.getvalue()).decode('ascii')

    # Small pixel image
    small_pixel_image = process_img_to_small_pixel(image_raw.copy()) # This one's useful for copy-pasting into art programs.
    byte_arr_small = io.BytesIO()
    small_pixel_image.save(byte_arr_small, format='PNG')
    encoded_image_small = base64.encodebytes(byte_arr_small.getvalue()).decode('ascii')

    # We make sure to also add the color palette too. That's important!
    return f'''
        {get_head()}
        <body>
            <button onclick="location.href='/'" class="homelink">BACK TO GENERATOR</button>
            <h1>{image_record.text.upper()}</h1>
            SOURCE IMAGE AND PSEUDO-PIXEL VERSION.
            <div class="permimagedisplay">
                <img src="data:image/png;base64,{encoded_image}"/>
                <img src="data:image/png;base64,{encoded_image_full}"/>
            </div><br><br>
            <div class="permimagedisplay">
                <div>
                    <img style="margin: 0px" src="data:image/png;base64,{encoded_image_small}"/><br>
                    <div style="font-size:9px">SMALL PIXEL IMAGE FOR COPYPASTING!</div>
                    <!--I just think it's funny when text is small sometimes. Don't do this, it's bad accessibility.--!>
                </div>
                <div class="colordisplay">
                    {color_array_html_render(small_pixel_image.convert("RGB").getcolors(maxcolors=16))}
                </div>
            </div>
        </body>'''

# Just some simple error pages.
def not_found_error():
    return f'''
        {get_head()}
        <body>
            <h1>404: NOT FOUND</h1>
            <p>Sorry, the image you're looking for doesn't exist. Please try again.</p>
        </body>'''

def database_failure_error():
    return f'''
        {get_head()}
        <body>
            <h1>500: DATABASE ERROR</h1>
            <p>Sorry, the database is down. Please try again later.</p>
        </body>'''


# This is briefly going to get a little technical, so bear with me, reviewer.
# Alt-z is your word-wrap, isn't it?
# If you know about the technical aspects of pixel art, or don't care to know the details, skip this block.
'''
There we go, this is a little more comfortable. Alright, so, generally-speaking one of the flaws of AI-generated pixel art (that is, the pixel art generated by an AI by appending the term "pixel art" to the prompt) is that it disobeys a lot of key constraints used in the pixel-art field due to most models being trained on more diverse data. One of the big ones that it ignores is color palette restrictions, since they're both uncommon and not immediately clear, plus few datasets make a point of noting them due to the fact that the data they're built with often includes aliasing and other similar issues due to scaling of the images when displayed online. Twitter and similar sites like to interfere with images in various ways, that's just how it is. Anyway: Palette restrictions are ignored. It ignores a lot of others too, but for now this is the important one. Color palette is typically more constrained in pixel art, originally due to hardware restrictions like limited memory but now due to a desire for a sort of visual consistency that depicts large blocks properly. With that in mind, we can't just resize, we also have to constrain the palette to some degree as well. The goal here is to force the model's output to work with some limited colors, and then the user can later use the palette interface to take those colors whenever they happen to be useful for personal work. This is a good way to get a lot of colors that work well together with a given concept.
'''
# Okay, back to business.
def process_img_to_full_pixel(image):
    return process_img_to_small_pixel(image).resize((512, 512))

def process_img_to_small_pixel(image):
    return image.convert("P", palette=Image.ADAPTIVE, colors=16).resize((128, 128)) # Reduce the palette to useful colors.

# You might be wondering: Why not quantize the colors instead? Why an adaptive palette reduction?
# Wouldn't that result in more web-safe colors, better snapping, and a more consistent palette?
# Because I just don't like how it looks, honestly. It's a little too "gameboy camera" for me! 
# Maybe a user-configured setting for the future, but not now.
# Actually you probably aren't wondering that to begin with. But I figured it bears mentioning.