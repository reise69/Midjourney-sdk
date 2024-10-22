import requests
import time
import json, random
import re
from pprint import pprint as pp
import uuid
from datetime import datetime
from PIL import Image
import os
from slugify import slugify


class Midjourney:
    API_URL = 'https://discord.com/api/v9'
    APPLICATION_ID = '936929561302675456'
    DATA_ID = '938956540159881230'
    DATA_VERSION = '1237876415471554623'
    

    def __init__(self, channel_id, oauth_token, session_id):
        self.channel_id = channel_id
        self.oauth_token = oauth_token
        self.session_id = session_id
        
        self.client = requests.Session()
        self.client.headers.update({
            'Authorization': oauth_token
        })

        response = self.client.get(f'{self.API_URL}/channels/{self.channel_id}')
        data = response.json()
        if 'guild_id' not in data:
            raise Exception('Channel not found, token value or session value are not valid. Please check your token and channel id.')
        
        self.guild_id = data['guild_id']

        response = self.client.get(f'{self.API_URL}/users/@me')
        data = response.json()

        self.user_id = data['id']

    @staticmethod
    def first_where(array, key, value=None):
        for item in array:
            if callable(key) and key(item):
                return item
            if isinstance(key, str) and item[key].startswith(value):
                return item
        return None

    def imagine(self, prompt):
        params = {
            'type': 2,
            'application_id': self.APPLICATION_ID,
            'guild_id': self.guild_id,
            'channel_id': self.channel_id,
            'session_id': self.session_id,
            'data': {
                'version': self.DATA_VERSION,
                'id': self.DATA_ID,
                'name': 'imagine',
                'type': 1,
                'options': [{
                    'type': 3,
                    'name': 'prompt',
                    'value': prompt
                }],
                'application_command': {
                    'id': self.DATA_ID,
                    'application_id': self.APPLICATION_ID,
                    'version': self.DATA_VERSION,
                    'default_member_permissions': None,
                    'type': 1,
                    'nsfw': False,
                    'name': 'imagine',
                    'description': 'Create images with Midjourney',
                    'dm_permission': True,
                    'options': [{
                        'type': 3,
                        'name': 'prompt',
                        'description': 'The prompt to imagine',
                        'required': True
                    }]
                },
                'attachments': []
            }
        }

        r = self.client.post(f'{self.API_URL}/interactions', json=params)
        # Print des erreurs

        # print(r.text)
        time.sleep(2)

        imagine_message = None

        count = 0
        while imagine_message is None:
            imagine_message = self.get_imagine(prompt, count)
            if imagine_message is None:
                time.sleep(8)
                # print(f"Retry {count}")
                count += 1

        return imagine_message

    def get_imagine(self, prompt, count=0):
        response = self.client.get(f'{self.API_URL}/channels/{self.channel_id}/messages')

        data = response.json()

        def criteria(item):

            # Just test if http is in prompt
            if "http" in prompt:
                # Replace all http(s)://... by <URL>
                prompt_test = re.sub(r'https?://\S+', '<URL>', prompt)
                item_content = re.sub(r'https?://\S+', 'URL>', item['content'])


                end_with = "fast"
                if "--relax" in prompt:
                    end_with = "relaxed"
                if "--turbo" in prompt:
                    end_with = "turbo"
                return (item_content.startswith(f"**{prompt_test}** - <@{self.user_id}>")
                        and "%" not in item['content']
                        and ((item['content'].endswith('(fast)')) or (item['content'].endswith(f'({end_with})'))))
            else:
                end_with = "fast"
                if "--relax" in prompt:
                    end_with = "relaxed"
                if "--turbo" in prompt:
                    end_with = "turbo"

                return (item['content'].startswith(f"**{prompt}** - <@{self.user_id}>")
                        and "%" not in item['content']
                        and ((item['content'].endswith('(fast)')) or (item['content'].endswith(f'({end_with})'))))

        raw_message = self.first_where(data, criteria)

        # Limit to 30 tries
        if raw_message is None and count < 30:
            return None

        if count == 30:

            return {
                'id': data[0]['id'],
                'prompt': prompt,
                'raw_message': data[0]
            }

        r_final = {
            'id': raw_message['id'],
            'prompt': prompt,
            'raw_message': raw_message
        }
        ""

        return r_final

    def upscale(self, message, upscale_index=0):
        if 'raw_message' not in message:
            raise Exception('Upscale requires a message object obtained from the imagine/getImagine methods.')
        if upscale_index < 0 or upscale_index > 3:
            raise Exception('Upscale index must be between 0 and 3.')

        upscale_hash = None
        raw_message = message['raw_message']

        if 'components' in raw_message and isinstance(raw_message['components'], list):
            upscales = raw_message['components'][0]['components']
            upscale_hash = upscales[upscale_index]['custom_id']

        params = {
            'type': 3,
            'guild_id': self.guild_id,
            'channel_id': self.channel_id,
            'message_flags': 0,
            'message_id': message['id'],
            'application_id': self.APPLICATION_ID,
            'session_id': self.session_id,
            'data': {
                'component_type': 2,
                'custom_id': upscale_hash
            }
        }

        self.client.post(f'{self.API_URL}/interactions', json=params)
        upscaled_photo_url = None

        count = 0
        while upscaled_photo_url is None:
            upscaled_photo_url = self.get_upscale(message, upscale_index, count)
            if upscaled_photo_url is None:
                time.sleep(3)
                count += 1

        return upscaled_photo_url

    def get_upscale(self, message, upscale_index=0, count=0):
        if 'raw_message' not in message:
            raise Exception('Upscale requires a message object obtained from the imagine/getImagine methods.')
        if upscale_index < 0 or upscale_index > 3:
            raise Exception('Upscale index must be between 0 and 3.')

        prompt = message['prompt']

        response = self.client.get(f'{self.API_URL}/channels/{self.channel_id}/messages')
        messages = response.json()

        # Delete --seed from prompt
        prompt = re.sub(r"\s--seed\s\d+", "", prompt)

        # Delete --relax from prompt
        prompt = re.sub(r"\s--relax", "", prompt)
        prompt = re.sub(r"\s--turbo", "", prompt)

        url = None

        prompt_test = re.sub(r'https?://\S+', '<URL>', prompt)
        messages[0]['content'] = re.sub(r'https?://\S+', 'URL>', messages[0]['content'])
        if messages[0]['content'].startswith(f"**{prompt_test}** - Image"):
            url = messages[0]['attachments'][0]['url']

        # Au bout de 5 essais on retourne messages[0]['attachments'][0]['url']
        if count == 3:
            print("force last url")
            return messages[0]['attachments'][0]['url']

        if url is None or url == "":
            return None
        else:
            return url

    # Options
    # --aspect or --ar // Aspect ratio of the output image
    # --chaos (0-100) // Chaos level of the output image
    # --fast // force fast mode
    # --iw: (0-3) for v 6.0 & (0.5 - 2) for v 5.0 // Weight if image source in input
    # --no // Negative prompting (try to remove elements in the image)
    # --quality or --q // (0.25, 0.5, 1) Quality of the output image (highter is the value, coster is the image)
    # --style (random, random-64, random-128) or switch between the styles (https://docs.midjourney.com/docs/models)
    # --relax // force relax mode
    # --repeat or --r (1-40) // lunch x times the same prompt
    # --seed // Seed for the random generation
    # --stop (10-100) // Stop the generation at X% of completion
    # --stylize (0-1000) // défault 100 for v 6.0
    # --tile (parameter generates images that can be used as repeating tiles to create seamless patterns.)
    # --turbo // force turbo mode
    # --video
    # --v (4, 5, 6.0) // Version of the model
    # --weird // 0-3000 // Weirdness level of the output image
    # sources['images'] = [url1, url2, url3] // List of images to use as input // Add before prompt
    # sources['caracters'] = [url1, url2, url3] // List of images of caracters to use as input // Add with the parameter --cref
    # sources['styles'] = [url1, url2, url3] // List of images of styles to use as input // Add with the parameter --sref

    def generate(self, prompt, options={}, sources={}, upscale_index=-1):

        prompt = prompt.strip()

        # Force options version to 6.0
        if "v" not in options or options['v'] == "":
            options['v'] = '6.1'

        if "ar" not in options or options['ar'] == "":
            options['ar'] = '3:2'

        if "seed" not in options or options['seed'] == "":
            options['seed'] = random.randint(0, 4294967295)

        # Force seed as last parameter in the dict
        seed = options.pop('seed')
        options['seed'] = seed

        parameter = ""
        no_value_key = ['relax', 'fast', 'turbo']
        for key, value in options.items():
            if key in no_value_key:
                parameter += f" --{key}"
            else:
                parameter += f" --{key} {value}"

        # Image sources
        if 'images' in sources:
            prompt = " ".join(sources['images']) + " " + prompt

        # Add caracters
        if 'caracters' in sources and len(sources['caracters']) > 0:
            prompt = prompt + " --cref " + " ".join(sources['caracters'])

        # Add styles
        if 'styles' in sources and len(sources['styles']) > 0:
            prompt = prompt + " --sref " + " ".join(sources['styles'])

        # On ajoute une seed pour éviter les doublons
        prompt = prompt + parameter

        imagine = self.imagine(prompt)

        # print(imagine)

        if upscale_index == -1:
            upscale_index = random.randint(0, 3)
        # print(upscale_index)
        upscaled_photo_url = self.upscale(imagine, upscale_index)

        return {
            'imagine_message_id': imagine['id'],
            'upscaled_photo_url': upscaled_photo_url
        }

    # get parameter from prompt str # return dict, clean prompt without parameters
    def get_parameter_from_prompt(self, prompt):

        sources = {}
        # Get all sources from prompt
        # Get --sref http://xxxx, http://xxxx, http://xxxx
        sources['styles'] = []
        styles_match = re.search(r'--sref\s+((?:https?://\S+(?:,\s*)?)+)', prompt)
        if styles_match:
            sources['styles'] = re.findall(r'https?://\S+', styles_match.group(0))
            prompt = prompt[:styles_match.start()] + prompt[styles_match.end():]

        # Get --cref http://xxxx, http://xxxx, http://xxxx
        sources['caracters'] = []
        caracters_match = re.search(r'--cref\s+((?:https?://\S+(?:,\s*)?)+)', prompt)
        if caracters_match:
            sources['caracters'] = re.findall(r'https?://\S+', caracters_match.group(0))
            prompt = prompt[:caracters_match.start()] + prompt[caracters_match.end():]

        # Get all parameters from prompt
        parameters = re.findall(r'--(\w+\s[\w.:]+)', prompt)
        # Clean prompt
        for parameter in parameters:
            prompt = prompt.replace(f'--{parameter}', '')

        # Delete multiple spaces
        prompt = re.sub(' {2,}', ' ', prompt)
        prompt = prompt.strip()
        return {parameter.split(' ')[0].replace('--', ''): parameter.split(' ')[1] for parameter in
                parameters}, sources, prompt

    
    def download_and_convert_image(self, image_url, image_name=None, save_path=None, compression=0.9, size=None, crop=False):
        try:
            response = self.client.get(image_url)
            response.raise_for_status()

            if image_name is None:
                image_name = f"{uuid.uuid4()}-{datetime.now().strftime('%d-%m-%Y')}"
            
            image_name = slugify(image_name)

            if save_path is None:
                save_path = os.getcwd()
            
            temp_png_path = os.path.join(save_path, f"{image_name}.png")

            with open(temp_png_path, 'wb') as f:
                f.write(response.content)

            with Image.open(temp_png_path) as img:
                if size is not None:
                    if crop:
                        target_ratio = size[0] / size[1]
                        
                        if img.width / img.height > target_ratio:
                            new_width = int(img.height * target_ratio)
                            offset = (img.width - new_width) // 2
                            img = img.crop((offset, 0, offset + new_width, img.height))
                        else:
                            new_height = int(img.width / target_ratio)
                            offset = (img.height - new_height) // 2
                            img = img.crop((0, offset, img.width, offset + new_height))
                    
                    
                    img = img.resize(size, Image.LANCZOS)
                

                jpg_path = os.path.join(save_path, f"{image_name}.jpg")

                img.convert("RGB").save(jpg_path, "JPEG", quality=int(compression * 100))

            os.remove(temp_png_path)

            return jpg_path
        except Exception as e:
            print(f"Error during image processing: {str(e)}")
            return False

if __name__ == "__main__":
    discord_channel_id = "XxxXxxXXxXxXx"
    discord_user_token = "XXXXXXxxXXXxXxxxxXxXXXXxXX"
    discord_session_id = "XxxXxxXXxXxXx"
    
    midjourney = Midjourney(discord_channel_id, discord_user_token, discord_session_id)

    prompt = "An illustration of A teddy bear in scotland, french flag in the hand, scotland landscape, comics, inspired by Ted movie --ar 3:2 --v 6.1 --fast"
    options, sources, prompt = midjourney.get_parameter_from_prompt(prompt)

    print(prompt)
    print(options)
    print(sources)

    message = midjourney.generate(prompt, options, sources)
    
    # Display selected image url
    print(message['upscaled_photo_url'])

    # Download and convert image to jpg on your computer
    download_path = "downloads"
    midjourney.download_and_convert_image(message['upscaled_photo_url'], "A Teddy bear in scotland", download_path, 0.9, (500, 500), True)
