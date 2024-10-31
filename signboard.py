# ... (previous imports remain the same)

class InfoCard:
    def __init__(self, title, description, image_path):
        self.title = title
        self.description = description
        self.image_path = image_path

class EmailSignboard:
    def __init__(self, email_address, password, imap_server, html_path, template_path, static_folder):
        # ... (previous initialization code)
        self.static_folder = static_folder
        self.info_cards = []

    def add_info_card(self, title, description, image_path):
        """Add an info card to the rotation"""
        self.info_cards.append(InfoCard(title, description, image_path))

    def update_webpage(self, posts):
        """Update the HTML file with new content and info cards"""
        template = self.env.get_template(self.template_name)
        
        # Prepare template data
        template_data = {
            'posts': posts,
            'info_cards': [
                {
                    'title': card.title,
                    'description': card.description,
                    'image': card.image_path
                } for card in self.info_cards
            ]
        }
        
        # Generate new HTML
        html_content = template.render(**template_data)
        
        # Write to file
        with open(self.html_path, 'w', encoding='utf-8') as f:
            f.write(html_content)

# Usage example
if __name__ == "__main__":
    signboard = EmailSignboard(
        email_address="your-email@example.com",
        password="your-password",
        imap_server="imap.gmail.com",
        html_path="signboard.html",
        template_path="signboard_template.html",
        static_folder="static"
    )

    # Add some example info cards
    signboard.add_info_card(
        "Safety First",
        "Our commitment to workplace safety is unwavering",
        "/static/images/safety.jpg"
    )
    signboard.add_info_card(
        "Quality Assurance",
        "Delivering excellence in every project",
        "/static/images/quality.jpg"
    )
    signboard.add_info_card(
        "Innovation",
        "Leading the way in packaging automation",
        "/static/images/innovation.jpg"
    )

    signboard.run()
