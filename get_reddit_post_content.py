import praw
import os
from dotenv import load_dotenv

load_dotenv()

# --- Recursive Comment Extractor ---
def extract_comments_recursively(comment_forest, level=0, max_limit=30, count_tracker=None):
    """Recursively digs through Reddit comments to maintain reply hierarchy."""
    if count_tracker is None:
        count_tracker = [0] # Use a list to pass the count by reference
        
    text = ""
    for comment in comment_forest:
        # Stop if we hit our desired comment limit
        if count_tracker[0] >= max_limit:
            break
            
        if isinstance(comment, praw.models.Comment) and comment.author and not comment.stickied:
            # Create blockquote indents based on how deep the reply is
            indent = "> " * level
            
            # Ensure multi-line comments stay properly indented
            body_indented = comment.body.replace('\n', f'\n{indent}')
            
            # Append the formatted comment
            text += f"{indent}**u/{comment.author.name}**:\n{indent}{body_indented}\n\n"
            count_tracker[0] += 1
            
            # If this comment has replies, process them by increasing the depth level
            if hasattr(comment, "replies"):
                text += extract_comments_recursively(comment.replies, level + 1, max_limit, count_tracker)
                
    return text


# --- Reddit Data Fetching ---
def get_reddit_post_content(post_url: str) -> tuple[str, str, str]:
    """Retrieves the title, ID, and structured content for a given Reddit post URL."""
    try:
        client_id = os.getenv("REDDIT_CLIENT_ID")
        client_secret = os.getenv("REDDIT_CLIENT_SECRET")
        username = os.getenv("REDDIT_USERNAME")
        user_agent = f"Post Extractor v1.2 by u/{username}"
        
        reddit = praw.Reddit(client_id=client_id, client_secret=client_secret, user_agent=user_agent)
        submission = reddit.submission(url=post_url)
        
        title = submission.title
        post_id = submission.id
        
        # Build the structured markdown text
        full_text = f"**Post Title:** {title}\n\n"
        
        if submission.selftext:
            full_text += f"**Body:**\n{submission.selftext}\n\n"
        
        full_text += "---\n**COMMENTS**\n\n"
        
        # Resolve all "Load more comments" instances
        submission.comments.replace_more(limit=0)
        
        # Pass the top-level comment forest to our new recursive function
        full_text += extract_comments_recursively(submission.comments)
        
        return title, post_id, full_text
        
    except Exception as e:
        return None, None, f"Error: Could not fetch Reddit post. Details: {e}"


# --- Main Execution Block ---
if __name__ == "__main__":
    OUTPUT_DIR = "reddit_extractions"
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    reddit_url = input("Please enter the Reddit Post URL to extract: ")
    print("--- Step 1: Fetching Post Content from Reddit ---")
    
    post_title, post_id, extracted_text = get_reddit_post_content(reddit_url)
    
    if extracted_text.startswith("Error:"):
        print(extracted_text)
        exit()
        
    print(f"Successfully fetched content for post: \"{post_title}\"")

    print(f"\n--- Step 2: Saving Report ---")
    
    # Save as an .md file
    output_filename = os.path.join(OUTPUT_DIR, f"{post_id}_extracted.md")
    
    with open(output_filename, 'w', encoding='utf-8') as f:
        f.write("**Extracted Reddit Post Content**\n\n")
        f.write(f"**Source URL:** {reddit_url}\n\n")
        f.write("---\n\n")
        f.write(extracted_text)
    
    print(f"\n✅ Content successfully saved to: '{output_filename}'")