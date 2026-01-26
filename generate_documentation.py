
from bs4 import BeautifulSoup

def generate_documentation():
    # Define the initial part of the narrative
    initial_narrative = """Oh, this is much better! I'm on a new website now, and it's much easier to find my way around. I'm trying to find the events, and I think I've found them.

I went straight to the events page, and there's a nice, clear list of upcoming events. It's not too cluttered, and I can see the dates and what the events are about. It's so much easier to read than that other website. I'm so glad I found this one. I can actually see what's going on! I'll have a good look through this list and see if there's anything I'd like to go to."""

    # Read the HTML log file
    try:
        with open("playwright_log.txt", "r", encoding="utf-8") as log_file:
            log_html = log_file.read()
    except FileNotFoundError:
        print("Error: playwright_log.txt not found. Please run the Playwright script first.")
        return

    # Parse the HTML to find the event details
    soup = BeautifulSoup(log_html, 'html.parser')

    # Find the accordion items which contain the events
    accordion_items = soup.find_all('li', class_='accordion-item')

    events_narrative = "\n\n--- Part 2: Looking at the Events ---\n\nAlright, let's have a look at what's on. I've made a little list for myself.\n\n"

    # Extract and process the event details
    chosen_event = None
    if accordion_items:
        for item in accordion_items:
            month_element = item.find('span', class_='accordion-item__title')
            if not month_element:
                continue
            month = month_element.get_text(strip=True)
            events_narrative += f"**{month}**\n"

            event_details = item.find_all('p')
            for p in event_details:
                event_text = p.get_text(strip=True)
                events_narrative += f"- {event_text}\n"

                # Let's add some "customer" judgment
                if "online" in event_text.lower():
                    events_narrative += "  - *My thoughts: An online class sounds nice. I can do that from home. That's a plus for me. I'd rate this one a 4 out of 5.*\n"
                elif "in person" in event_text.lower() or "residential" in event_text.lower():
                    events_narrative += "  - *My thoughts: A retreat sounds lovely, but I'm not sure about traveling. I'll give this a 3 out of 5 for now.*\n"

                # Let's say the customer decides on the first "online class" they find
                if "online class" in event_text.lower() and not chosen_event:
                    link_element = p.find('a')
                    chosen_event = {
                        "text": event_text,
                        "link": link_element['href'] if link_element else None
                    }
    else:
        events_narrative += "I couldn't find a list of events. It seems the page is structured differently than I thought. Oh, well. I'll have to come back and try again later.\n"

    events_narrative += "\n**My Decision**\n"
    if chosen_event:
        events_narrative += f"I think I'll go with this one: '{chosen_event['text']}'. It's an online class, which is perfect for me. Now, how do I sign up for it?\n"
        if chosen_event['link']:
            events_narrative += f"There's a link here. I'll click on it and see where it takes me. The link is: {chosen_event['link']}\n"
            events_narrative += "I'm not sure what to do next, but I'll give it a try. Wish me luck!\n"
        else:
            events_narrative += "Oh, dear. It says the registration link is to come. I suppose I'll have to check back later. That's a bit of a shame.\n"
    else:
        events_narrative += "I've had a good look, but I'm not sure which one to choose just yet. I'll have to think about it a bit more.\n"

    # Combine the initial narrative with the new section
    full_documentation = initial_narrative + events_narrative

    # Write the expanded documentation to the file
    with open("customer_documentation.txt", "w", encoding="utf-8") as doc_file:
        doc_file.write(full_documentation)

if __name__ == "__main__":
    generate_documentation()
