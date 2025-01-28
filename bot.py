#..........This Bot Made By [RAHAT](https://t.me/r4h4t_69)..........#
#..........Anyone Can Modify This As He Likes..........#
#..........Just one requests do not remove my credit..........#



import aiohttp
import asyncio
import os
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from PIL import Image
from io import BytesIO
from bs4 import BeautifulSoup
from fpdf import FPDF
import shutil

api_id = '' # Add Your Telegram API_ID Here
api_hash = '' # Add Your Telegram API_ID Here
bot_token = '' # Add Your Telegram API_ID Here

app = Client("manga_search_bot", api_id=api_id, api_hash=api_hash, bot_token=bot_token)

manga_data = {}  # Store manga data using series_slug as key
short_slug_map = {}  # Map short slugs to series_slug
chapter_data = {}  # Store chapter data for callback handling
user_tasks = {}  # To store active download tasks per user

# Create a queue for download tasks
download_queue = asyncio.Queue()


async def search_manga(manga_name):
    base_url = "https://api.reaperscans.com/query"
    #params = {"adult": "true", "query_string": manga_name} #Use This For Both Novel And Comic
    params = {"adult": "true", "series_type": "Comic", "query_string": manga_name} #Use This For Comic Only

    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(base_url, params=params) as response:
                response.raise_for_status()
                data = await response.json()

                if data["meta"]["total"] > 0:
                    results = []
                    for index, manga in enumerate(data["data"][:100]):
                        title = manga["title"]
                        description = manga["description"][:1000] + "..."
                        chapters = len(manga["free_chapters"])
                        series_type = manga["series_type"]
                        thumbnail = manga['thumbnail']
                        if not thumbnail.startswith("https://media.reaperscans.com/"):
                            thumbnail = f"https://media.reaperscans.com/file/4SRBHm/{thumbnail}"
                        manga_link = f'https://reaperscans.com/series/{manga["series_slug"]}'

                        # Store the manga data in the dictionary and use index as short slug
                        short_slug = str(index)
                        short_slug_map[short_slug] = manga["series_slug"]
                        manga_data[manga["series_slug"]] = {
                            "title": title,
                            "description": description,
                            "link": manga_link,
                            "total_ch": chapters,
                            "thumbnail": thumbnail,
                            "type" : series_type,
                            "chapters": manga["free_chapters"]
                        }
                        # Append (title, short_slug) to results
                        results.append((title, short_slug))
                    return results
                else:
                    return []
        except aiohttp.ClientError as e:
            return f"An error occurred: {e}"

async def fetch_chapter_content(series_type, chapter_url):
    async with aiohttp.ClientSession() as session:
        async with session.get(chapter_url) as response:
            if response.status != 200:
                print(f"Failed to retrieve the page. Status code: {response.status}")
                return None
            
            content = await response.text()
            soup = BeautifulSoup(content, 'html.parser')

            if series_type == 'Novel':
                # Attempt to extract text content for novels using script tags
                script_tags = soup.find(lambda tag: tag.name == 'script' and tag.string and 
                         tag.string.startswith('self.__next_f.push') and 'REAPER SCANS' in tag.string)
                
                for script in script_tags:
                    if script.string and script.string.startswith('self.__next_f.push') and 'REAPER SCANS' in script.string:
                        text_content = script.string
                        
                        # Remove unwanted substrings
                        unwanted_substrings = [
                            "u003cbr", "style", "line", "height", "u003ewang", "u003cstrong",
                            "u003ca", "u003cem", "strong", "/p", "/em", "(1)", "u003cp"
                            "\\r\\n", "u0026nbsp", "u0026ndash", "u0026ldquo", "u0026hellip", "u0026rsquo", 
                            "u0026rdquo", "u003c", "u0026mdash", "u0026lsquo", "u003ewei", "2;", "1;", 
                            "u003e", "/", "\\", "=", ":", "\"", "self.__next_f.push", "(", ")", "[", "]",
                            "1,", "-", ";", "hrefhttpsdiscord.cominvitereaperscanshttpsdiscord.cominvitereaperscansa", "span", "REAPER SCANS"
                        ]
                        
                        for unwanted in unwanted_substrings:
                            text_content = text_content.replace(unwanted, "")
                        
                        return text_content.strip()  # Return cleaned text content
                        
                print("Failed to find novel content in the page.")
                return None
            
            else:
                # For manga, fetch the images
                containers = soup.find_all('div', class_='container')
                images = []

                for container in containers:
                    imgs = container.find_all('img')
                    for img in imgs:
                        srcset = img.get('src')
                        if srcset:
                            first_srcset = srcset.split(',')[0].strip()
                            url_only = first_srcset.split(' ')[0]

                            if "media.reaperscans.com" in url_only and "jpg" in url_only:
                                cleaned_url = url_only.replace("/_next/image?url=", "").split("&")[0]
                                cleaned_url = cleaned_url.replace("%3A%2F%2F", "://")
                                cleaned_url = cleaned_url.replace("%2Ffile%2F", "/file/")
                                cleaned_url = cleaned_url.replace("%2F", "/")
                                cleaned_url = cleaned_url.replace("%25", "%")

                                images.append(cleaned_url)

                return images


async def create_pdf_from_text(user_id, series_slug, chapter_slug, text_content):
    manga = manga_data.get(series_slug)
    chapter_name = chapter_slug.replace('-', ' ').title()  # Cleaner chapter name

    download_folder = f'downloads/{user_id}/{series_slug}/{chapter_slug}'
    if not os.path.exists(download_folder):
        os.makedirs(download_folder)

    pdf_filename = f"{manga['title']} [{chapter_name}].pdf"
    pdf_path = os.path.join(download_folder, pdf_filename)

    # Create a PDF using FPDF
    pdf = FPDF()
    pdf.add_page()

    # Set the font to a Unicode-compliant font (DejaVuSans)
    pdf.add_font('DejaVu', '', 'DejaVuSans.ttf', uni=True)
    pdf.set_font('DejaVu', '', 12)

    # Add text content to the PDF
    for line in text_content.split('\n'):
        pdf.multi_cell(0, 10, line)

    # Save the PDF
    pdf.output(pdf_path)
    print(f"PDF created successfully: {pdf_path}")

    return pdf_path, None


async def create_pdf_from_images(user_id, series_slug, chapter_slug, images):
    manga = manga_data.get(series_slug)
    chapter_name = chapter_slug.replace('-', ' ').title()  # Cleaner chapter name

    download_folder = f'downloads/{user_id}/{series_slug}/{chapter_slug}'
    pdf_images = []
    thumbnail_image = None  # This will hold the first image (used as thumbnail)

    if not os.path.exists(download_folder):
        os.makedirs(download_folder)

    async with aiohttp.ClientSession() as session:
        for index, img_url in enumerate(images):
            try:
                async with session.get(img_url) as resp:
                    if resp.status == 200:
                        content_type = resp.headers.get('Content-Type', '')
                        if 'image' in content_type:
                            img_data = await resp.read()
                            try:
                                img = Image.open(BytesIO(img_data)).convert('RGB')
                                image_path = os.path.join(download_folder, f'image_{index}.jpg')
                                img.save(image_path)
                                pdf_images.append(image_path)

                                # Save the first image as the thumbnail
                                if index == 0:
                                    thumbnail_image = img

                                print(f"Downloaded and saved image: {img_url}")
                            except Exception as e:
                                print(f"Error processing image {img_url}: {e}")
                        else:
                            print(f"Invalid content type for {img_url}: {content_type}")
                    else:
                        print(f"Failed to download image: {img_url}, status: {resp.status}")
            except Exception as e:
                print(f"Error fetching image {img_url}: {e}")

    pdf_filename = f"{manga['title']} [{chapter_name}].pdf"
    pdf_path = os.path.join(download_folder, pdf_filename)

    if pdf_images:
        try:
            images_list = [Image.open(image_path) for image_path in pdf_images]
            images_list[0].save(pdf_path, save_all=True, append_images=images_list[1:])
            print(f"PDF created successfully: {pdf_path}")
        except Exception as e:
            print(f"Error saving PDF: {e}")
    else:
        print("No images available to create a PDF.")

    thumbnail_path = os.path.join(download_folder, "thumbnail.jpg")
    if thumbnail_image:
        thumbnail_image.thumbnail((320, 320))  # Set the thumbnail size
        thumbnail_image.save(thumbnail_path, "JPEG")
        print(f"Thumbnail created successfully: {thumbnail_path}")

    return pdf_path, thumbnail_path



user_tasks = {}

async def worker():
    while True:
        # Check the global queue for any pending tasks
        task = await download_queue.get()
        
        # Get the task details: (user_id, series_slug, chapter_slug)
        user_id, series_slug, chapter_slug = task

        # Check if the user has an existing queue, and if not, create one
        if user_id not in user_tasks:
            user_tasks[user_id] = asyncio.Queue()

        # Add the new task to the user's specific queue
        await user_tasks[user_id].put((series_slug, chapter_slug))

        # Process the task for the user
        try:
            await process_user_download(user_id)
        except Exception as e:
            print(f"Error processing task {task}: {e}")
        
        download_queue.task_done()
        
async def process_user_download(user_id):
    """Process downloads for a specific user."""
    user_queue = user_tasks[user_id]

    while not user_queue.empty():
        series_slug, chapter_slug = await user_queue.get()
        manga = manga_data.get(series_slug)

        chapter_url = f"https://reaperscans.com/series/{series_slug}/{chapter_slug}"
        content = await fetch_chapter_content(manga['type'], chapter_url)

        if content:
            if manga['type'] == 'Novel':
                # Process novel text
                pdf_file, _ = await create_pdf_from_text(user_id, series_slug, chapter_slug, content)

                # Use manga thumbnail as PDF thumbnail
                thumbnail_url = manga['thumbnail']

                # Fetch the thumbnail from the URL
                async with aiohttp.ClientSession() as session:
                    async with session.get(thumbnail_url) as response:
                        if response.status == 200:
                            thumbnail_data = await response.read()
                            thumbnail_image = BytesIO(thumbnail_data)
                        else:
                            thumbnail_image = None  # In case thumbnail fetching fails

                # Send the PDF with the fetched thumbnail
                await app.send_document(
                    user_id,
                    pdf_file,
                    thumb=thumbnail_image,  # Send the manga thumbnail as the PDF thumbnail
                    caption="Here is your novel chapter!"
                )
            else:
                # Process manga images
                pdf_file, thumbnail = await create_pdf_from_images(user_id, series_slug, chapter_slug, content)

                # Send the PDF with the generated thumbnail
                await app.send_document(
                    user_id,
                    pdf_file,
                    thumb=thumbnail,  # Use the thumbnail image here
                    caption="Here is your manga chapter!"
                )

            # Cleanup the downloaded files
            download_folder = f'downloads/{user_id}/{series_slug}/{chapter_slug}'
            shutil.rmtree(download_folder, ignore_errors=True)

        # Mark the task as done
        user_queue.task_done()

    # Once the queue is empty, remove the user from the user_tasks dictionary
    del user_tasks[user_id]



@app.on_message(filters.command('start'))
async def start(client, message):
    welcome_message = "Welcome to the Manga Search Bot! Type /search <manga_name> to search for manga."
    await message.reply(welcome_message)



@app.on_message(filters.command('help'))
async def help(client, message):
    help_message = (
        "Here are the commands you can use:\n"
        "/search <manga_name> - Search for a manga.\n"
        "Click on a manga title to view more details.\n"
        "/queue - To see currently Active tasks in bot"
    )
    await message.reply(help_message)


@app.on_message(filters.command('search'))
async def handle_search(client, message):
    manga_name = message.text[len("/search "):].strip()
    if not manga_name:
        await message.reply("Please provide the name of the manga to search.")
        return
    results = await search_manga(manga_name)
    if not results:
        await message.reply("No manga found with that name.")
        return
    buttons = [
        [InlineKeyboardButton(title, callback_data=short_slug)]
        for title, short_slug in results
    ][:50]
    reply_markup = InlineKeyboardMarkup(buttons)

    await message.reply("Select a manga to see more details:", reply_markup=reply_markup)


@app.on_message(filters.command('queue'))
async def queue_status(client, message):
    # Get the size of the queue
    queue_size = download_queue.qsize()
    
    # Send the reply with the number of active download tasks
    if queue_size == 0:
        await message.reply("There are no active tasks in the queue.")
    else:
        await message.reply(f"There are currently {queue_size} tasks in the download queue.")


@app.on_callback_query()
async def handle_callback(client, callback_query):
    user_id = callback_query.from_user.id
    await callback_query.answer()

    # Check if the callback data corresponds to a manga selection
    if callback_query.data in short_slug_map:
        short_slug = callback_query.data
        series_slug = short_slug_map[short_slug]
        manga = manga_data.get(series_slug)

        if manga:
            # Buttons for viewing the manga or its chapters
            buttons = [
                [InlineKeyboardButton("Read Now", url=manga["link"]),
                 InlineKeyboardButton("All Chapters", callback_data=f"chapters:{short_slug}:0")]
            ]
            reply_markup = InlineKeyboardMarkup(buttons)

            # Format the response message with manga details
            response_message = (
                f"<blockquote><b>• {manga['title']}</b></blockquote>\n"
                f"<b>Manga Url :</b> <code>{manga['link']}</code>\n\n"
                f"<blockquote><b>Chapters : {manga['total_ch']}</b></blockquote>\n"
                f"<blockquote><b>Type : {manga['type']} </b></blockquote>\n"
                f"<b>Description:</b>\n"
                f"<pre>{manga['description']}</pre>"
                f"\n\n<blockquote><b>• Coded By RA H AT</b></blockquote>"
            )

            # Send the manga details along with the thumbnail image
            await callback_query.message.reply_photo(
                photo=manga["thumbnail"],
                caption=response_message,
                reply_markup=reply_markup
            )

    # Handle chapter list navigation
    elif callback_query.data.startswith("chapters:"):
        _, short_slug, offset_str = callback_query.data.split(":")
        offset = int(offset_str)
        series_slug = short_slug_map[short_slug]
        manga = manga_data.get(series_slug)

        if manga:
            # Create buttons for each chapter in the current offset range
            chapters = manga["chapters"]
            chapter_buttons = [
                [InlineKeyboardButton(chapter["chapter_name"], callback_data=f"chapter:{short_slug}:{chapter['chapter_slug']}")]
                for chapter in chapters[offset:offset + 10]
            ]

            # "Full Page" button
            full_page_button = [InlineKeyboardButton("Full Page", callback_data=f"full_page:{short_slug}:{offset}:{offset + 10}")]

            # Navigation buttons (for going forward or backward through chapter list)
            navigation_buttons = []
            if offset > 0:
                navigation_buttons.append(InlineKeyboardButton("<", callback_data=f"chapters:{short_slug}:{offset - 10}"))
            if offset + 10 < len(chapters):
                navigation_buttons.append(InlineKeyboardButton(">", callback_data=f"chapters:{short_slug}:{offset + 10}"))

            # Add the "Full Page" button between the chapters and navigation buttons
            if navigation_buttons:
                chapter_buttons.append(full_page_button)
                chapter_buttons.append(navigation_buttons)
            else:
                chapter_buttons.append(navigation_buttons)
                chapter_buttons.append(full_page_button)  # Full Page button goes before the nav buttons

            # Update the reply markup with the new chapter buttons
            reply_markup = InlineKeyboardMarkup(chapter_buttons)
            await callback_query.message.edit_reply_markup(reply_markup=reply_markup)

    # Handle "Full Page" button click
    elif callback_query.data.startswith("full_page:"):
        _, short_slug, start_offset_str, end_offset_str = callback_query.data.split(":")
        start_offset = int(start_offset_str)
        end_offset = int(end_offset_str)
        series_slug = short_slug_map[short_slug]
        manga = manga_data.get(series_slug)

        if manga:
            chapters = manga["chapters"][start_offset:end_offset]

            # Sort chapters by slug in reverse order (from lowest to highest chapter)
            chapters_sorted = sorted(chapters, key=lambda ch: ch['chapter_slug'])

            # Add each chapter to the download queue, one by one in reverse order (lowest to highest)
            for chapter in chapters_sorted:
                await download_queue.put((user_id, series_slug, chapter['chapter_slug']))

            # Notify the user that their chapters are being processed
            await callback_query.message.reply(f"All chapters from {chapters_sorted[0]['chapter_name']} to {chapters_sorted[-1]['chapter_name']} are being processed. They will be sent shortly.")

    # Handle individual chapter download
    elif callback_query.data.startswith("chapter:"):
        _, short_slug, chapter_slug = callback_query.data.split(":")
        series_slug = short_slug_map[short_slug]

        # Add the download task to the global download queue
        await download_queue.put((user_id, series_slug, chapter_slug))

        # Print log or notify in terminal
        print(f"Queue Added: {series_slug} {chapter_slug} for User {user_id}")

        # Notify the user that their download is being processed
        await callback_query.message.reply("Your chapter is being processed. It will be sent shortly.")
        

if __name__ == "__main__":
    # Start the worker in the background
    
    asyncio.get_event_loop().create_task(worker())  # Run the worker as a background task
    app.run()  # Keep the bot running
    
