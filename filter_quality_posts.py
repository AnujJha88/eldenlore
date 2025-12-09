"""
AGGRESSIVE LORE FILTER
Removes all noise and keeps ONLY lore-relevant posts
"""
import json
import sys

INPUT_FILE = 'lore_data.json'
OUTPUT_FILE = 'lore_data_filtered.json'

# Strict quality criteria
MIN_BODY_LENGTH = 300  # At least 300 characters (substantial content)
MIN_SCORE = 5  # At least 5 upvotes

# MUST contain at least 2 of these lore keywords
LORE_KEYWORDS = [
    'lore', 'theory', 'timeline', 'story', 'explained', 'analysis', 'interpretation',
    'marika', 'radagon', 'ranni', 'miquella', 'malenia', 'mohg', 'godwyn', 'godfrey',
    'erdtree', 'greater will', 'outer god', 'elden ring', 'shattering', 'elden lord',
    'demigod', 'empyrean', 'tarnished', 'grace', 'rune', 'ending', 'age of',
    'crucible', 'dragon', 'godskin', 'numen', 'nox', 'eternal city', 'nokron', 'nokstella',
    'frenzied flame', 'three fingers', 'two fingers', 'elden beast', 'radabeast',
    'radahn', 'morgott', 'rykard', 'messmer', 'melina', 'millicent', 'renna',
    'destined death', 'black flame', 'gloam-eyed', 'maliketh', 'gurranq',
    'placidusax', 'farum azula', 'beastman', 'dragon communion',
    'fell god', 'fire giant', 'forge', 'flame of ruin',
    'formless mother', 'blood star', 'mohgwyn', 'dynasty',
    'rot', 'scarlet', 'unalloyed', 'needle', 'haligtree',
    'carian', 'raya lucaria', 'moon', 'rennala', 'sorcery',
    'golden order', 'fundamentalism', 'corhyn', 'goldmask',
    'deathroot', 'those who live in death', 'tibia mariner',
    'ancestral', 'siofra', 'ainsel', 'spirit', 'mimic',
    'albinauric', 'latenna', 'lobo', 'phillia',
    'jar', 'alexander', 'living jar', 'potentate',
    'dung eater', 'omen', 'curse', 'seedbed',
    'volcano manor', 'recusant', 'tanith', 'rya',
    'roundtable', 'gideon', 'nepheli', 'fia', 'rogier',
    'varre', 'white mask', 'bloody finger',
    'shabriri', 'hyetta', 'irina', 'edgar',
    'sellen', 'thops', 'azur', 'lusat',
    'hewg', 'smithing', 'mending rune',
    'trina', 'sleep', 'dream', 'torch',
    'serpent', 'blasphemous', 'rykard',
    'gelmir', 'praetor', 'inquisitor'
]

# INSTANT REJECT - these phrases mean it's NOT lore
JUNK_PHRASES = [
    # Gameplay help
    'help me', 'stuck on', 'can\'t beat', 'how do i beat', 'tips for',
    'struggling with', 'need help', 'any tips', 'advice needed',
    
    # Build/stats
    'build advice', 'weapon recommendation', 'best build', 'stat allocation',
    'respec', 'what weapon', 'which weapon', 'best weapon for',
    'strength build', 'dex build', 'int build', 'faith build',
    'quality build', 'hybrid build', 'op build', 'meta build',
    
    # PvP/Multiplayer
    'pvp', 'invasion', 'invader', 'co-op', 'coop', 'summon', 'password',
    'dueling', 'arena', 'gank', 'host', 'phantom',
    
    # Trading/Requests
    'looking for', 'trade', 'giveaway', 'free runes', 'can someone drop',
    'anyone have', 'spare', 'duplicate', 'mule',
    
    # Achievement/Progress
    'just beat', 'just killed', 'finally beat', 'first time', 'i did it',
    'platinum', 'achievement', 'trophy', 'all bosses',
    
    # Questions without substance
    'is it worth', 'should i', 'when should', 'where do i go',
    'what level', 'how many', 'which one', 'better than',
    
    # Memes/Low effort
    'unpopular opinion', 'hot take', 'change my mind', 'am i the only one',
    'does anyone else', 'dae', 'literally unplayable',
    
    # Technical issues
    'fps', 'performance', 'crash', 'bug', 'glitch', 'error',
    'won\'t launch', 'black screen', 'stuttering',
    
    # Fashion/Screenshots
    'my character', 'fashion souls', 'drip', 'bling',
    'screenshot', 'photo mode', 'look at',
    
    # Sales/Price
    'on sale', 'worth buying', 'price', 'discount', 'steam sale'
]

# Posts with ONLY these words are usually low quality
TITLE_RED_FLAGS = [
    'question', 'help', 'confused', 'stuck', 'tips', 'advice',
    'build', 'weapon', 'best', 'op', 'broken', 'easy mode'
]

def is_lore_post(post):
    """Strict lore filter - only keeps genuine lore content"""
    
    title = post.get('title', '').lower()
    body = post.get('body', '').lower()
    text = title + ' ' + body
    
    # 1. Minimum length check
    if len(body) < MIN_BODY_LENGTH:
        return False
    
    # 2. Minimum score check
    if post.get('score', 0) < MIN_SCORE:
        return False
    
    # 3. INSTANT REJECT if contains junk phrases
    for junk in JUNK_PHRASES:
        if junk in text:
            return False
    
    # 4. Check if title is just a red flag word
    title_words = title.split()
    if len(title_words) <= 3 and any(flag in title for flag in TITLE_RED_FLAGS):
        return False
    
    # 5. MUST contain at least 2 lore keywords (strict requirement)
    keyword_count = sum(1 for keyword in LORE_KEYWORDS if keyword in text)
    if keyword_count < 2:
        return False
    
    # 6. Body must have some depth (not just a question)
    sentences = body.split('.')
    if len(sentences) < 3:  # At least 3 sentences
        return False
    
    # 7. Check for question marks - if too many, probably just asking for help
    question_marks = text.count('?')
    if question_marks > 3 and len(body) < 500:
        return False
    
    return True

def filter_posts():
    # Check which file to use
    if len(sys.argv) > 1:
        input_file = sys.argv[1]
    else:
        input_file = INPUT_FILE
    
    print(f"Loading posts from {input_file}...")
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            all_posts = json.load(f)
    except FileNotFoundError:
        print(f"❌ File not found: {input_file}")
        print("Available files:")
        import os
        for f in os.listdir('.'):
            if f.endswith('.json'):
                print(f"  - {f}")
        return
    
    print(f"Total posts: {len(all_posts)}")
    print("Applying AGGRESSIVE lore filter...")
    print()
    
    # Filter
    lore_posts = []
    removed_examples = []
    
    for post in all_posts:
        if is_lore_post(post):
            lore_posts.append(post)
        elif len(removed_examples) < 5:
            removed_examples.append(post['title'])
    
    print(f"✅ Lore posts: {len(lore_posts)}")
    print(f"❌ Removed: {len(all_posts) - len(lore_posts)}")
    print()
    
    if removed_examples:
        print("Examples of removed posts:")
        for title in removed_examples:
            print(f"  ❌ {title[:70]}...")
        print()
    
    # Sort by score
    lore_posts.sort(key=lambda x: x['score'], reverse=True)
    
    # Save
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(lore_posts, f, indent=2)
    
    print(f"💾 Saved to {OUTPUT_FILE}")
    print()
    print("Stats:")
    if lore_posts:
        print(f"  Average score: {sum(p['score'] for p in lore_posts) / len(lore_posts):.0f}")
        print(f"  Average length: {sum(len(p['body']) for p in lore_posts) / len(lore_posts):.0f} chars")
        print()
        print("Top 10 lore posts:")
        for i, post in enumerate(lore_posts[:10], 1):
            print(f"  {i}. [{post['score']:4d}] {post['title'][:65]}...")
    else:
        print("  ⚠️  No posts passed the filter!")

if __name__ == "__main__":
    filter_posts()
