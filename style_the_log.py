
from tiny_styler import TinyStyler

def style_log():
    # Read the content of the log file
    with open("playwright_log.txt", "r") as log_file:
        log_content = log_file.read()

    # Instantiate the styler
    styler = TinyStyler()

    # Define the style persona
    style = "A 60-year-old customer who is having difficulties navigating the web. They are not very tech-savvy and find the website confusing. They are trying to find the latest events."

    # Apply the style
    styled_content = styler.apply_style(content=log_content, style=style)

    # Write the styled content to the output file
    with open("customer_documentation.txt", "w") as doc_file:
        if styled_content:
            doc_file.write(styled_content)
        else:
            doc_file.write("Failed to style the content.")

if __name__ == "__main__":
    style_log()
