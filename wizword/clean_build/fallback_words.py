"""
Fallback word dictionary for when the OpenRouter API is unavailable.
Words are organized by subject and length.
Each category has 200 words (25 words per length from 3-10 letters).
"""

import random
from typing import Dict, List, Optional
import logging

FALLBACK_WORDS: Dict[str, Dict[int, List[str]]] = {
    "general": {
        3: ["cat", "dog", "hat", "run", "sky", "art", "box", "cup", "day", "eye", "fun", "gem", "hip", "ice", "joy", "key", "lip", "map", "now", "oak", "pen", "red", "sun", "top", "way"],
        4: ["book", "time", "love", "life", "home", "hope", "mind", "soul", "star", "tree", "wind", "bird", "door", "fire", "gold", "moon", "rain", "seed", "song", "wave", "year", "zone", "bell", "card", "desk"],
        5: ["house", "world", "peace", "happy", "smart", "dream", "earth", "faith", "grace", "heart", "light", "music", "ocean", "power", "quiet", "smile", "space", "storm", "truth", "voice", "water", "youth", "cloud", "dance", "flame"],
        6: ["garden", "nature", "family", "friend", "simple", "beauty", "bridge", "canvas", "dragon", "energy", "forest", "heaven", "island", "jungle", "legend", "memory", "mirror", "palace", "rhythm", "shadow", "spirit", "sunset", "temple", "valley", "wonder"],
        7: ["freedom", "harmony", "journey", "success", "wonder", "balance", "courage", "destiny", "eclipse", "fantasy", "gravity", "history", "insight", "justice", "mystery", "passion", "rainbow", "silence", "thunder", "unity", "victory", "whisper", "wisdom", "zenith", "horizon"],
        8: ["universe", "infinity", "kindness", "strength", "learning", "adventure", "blessing", "creation", "devotion", "eternity", "festival", "gratitude", "heritage", "innocent", "judgment", "kingdom", "laughter", "mountain", "paradise", "question", "radiance", "serenity", "treasure", "virtuous", "wellness"],
        9: ["adventure", "discovery", "knowledge", "happiness", "beautiful", "butterfly", "celebrate", "delightful", "enchanted", "fortunate", "graceful", "harmonica", "innocent", "jubilant", "kindness", "laughter", "majestic", "nostalgia", "peaceful", "radiance", "serenity", "timeless", "universe", "virtuous", "wanderer"],
        10: ["friendship", "experience", "technology", "creativity", "innovation", "aspiration", "brilliance", "confidence", "dedication", "enthusiasm", "fascinated", "generosity", "happiness", "integrity", "joyfulness", "knowledge", "leadership", "motivation", "optimistic", "passionate", "resilient", "sincerity", "thoughtful", "wonderful", "zealousness"]
    },
    "movies": {
        3: ["act", "cut", "set", "cam", "dvd", "art", "cgi", "hit", "vhs", "win", "box", "cam", "dir", "pan", "pro", "rip", "rom", "sci", "sfx", "spy", "sxf", "vfx", "vid", "vod", "wow"],
        4: ["film", "star", "cast", "role", "plot", "acts", "beat", "clip", "disc", "epic", "film", "hero", "idol", "lens", "lead", "mask", "noir", "play", "reel", "saga", "take", "view", "wrap", "zoom", "shot"],
        5: ["actor", "scene", "drama", "movie", "stage", "award", "block", "cinema", "drama", "extra", "frame", "genre", "humor", "image", "judge", "light", "media", "movie", "opera", "print", "quote", "scene", "theme", "voice", "watch"],
        6: ["action", "comedy", "horror", "script", "studio", "acting", "camera", "cinema", "direct", "editor", "finale", "golden", "horror", "impact", "movie", "motion", "output", "parody", "review", "screen", "talent", "visual", "writer", "drama", "scene"],
        7: ["actress", "musical", "romance", "thriller", "western", "academy", "casting", "classic", "comedy", "credits", "digital", "fantasy", "feature", "filming", "graphic", "montage", "preview", "release", "romance", "scoring", "script", "studio", "talent", "trailer", "viewing"],
        8: ["director", "producer", "scenario", "shooting", "suspense", "animated", "audience", "backstage", "cameraman", "cinematic", "climactic", "dramatic", "festival", "filmmaker", "lighting", "location", "narrative", "original", "premiere", "producer", "scenario", "sequence", "showcase", "spectacle", "thriller"],
        9: ["animation", "hollywood", "narrative", "screening", "storyline", "adventure", "broadcast", "character", "cinematic", "directing", "dramatic", "emotional", "filmmaker", "hollywood", "lighting", "narrative", "performer", "premiere", "producer", "scenario", "screening", "sequence", "spotlight", "suspense", "theatrical"],
        10: ["production", "screenplay", "soundtrack", "storyboard", "television", "adaptation", "background", "cinematics", "collection", "commercial", "documentary", "filmmaking", "historical", "independent", "melodrama", "performance", "production", "projection", "screenplay", "soundtrack", "storyboard", "theatrical", "videography", "widescreen", "directing"]
    },
    "music": {
        3: ["pop", "rap", "mix", "jam", "hit", "amp", "alt", "bpm", "dub", "ear", "gig", "hum", "key", "mic", "mix", "pop", "rap", "rif", "sax", "tap", "vox", "wav", "wah", "yip", "zen"],
        4: ["band", "beat", "song", "tune", "rock", "alto", "band", "bass", "beat", "bell", "drum", "duet", "folk", "funk", "jazz", "keys", "live", "note", "play", "rock", "song", "tune", "tone", "trio", "wind"],
        5: ["album", "audio", "blues", "dance", "music", "album", "audio", "beats", "blues", "chord", "dance", "disco", "drums", "flute", "genre", "music", "notes", "piano", "radio", "scale", "sound", "tempo", "tenor", "vocal", "voice"],
        6: ["chorus", "guitar", "lyrics", "rhythm", "singer", "artist", "backup", "chorus", "classic", "drums", "guitar", "melody", "music", "octave", "player", "record", "rhythm", "single", "stereo", "string", "tempo", "treble", "violin", "vocals", "waltz"],
        7: ["concert", "musical", "orchestra", "singing", "soprano", "acoustic", "ambient", "backing", "baroque", "classic", "concert", "country", "harmony", "karaoke", "maestro", "melody", "musical", "perform", "singing", "soprano", "techno", "timbre", "tremolo", "vibrato", "volume"],
        8: ["composer", "drumming", "festival", "keyboard", "musician", "acoustic", "amplifier", "arranger", "bassline", "classical", "composer", "concert", "conductor", "drumming", "ensemble", "festival", "harmony", "keyboard", "listener", "musician", "orchestra", "practice", "recorder", "symphony", "vocalist"],
        9: ["conductor", "ensemble", "orchestra", "recording", "symphony", "acapella", "accordion", "amplified", "arranging", "classical", "composing", "conductor", "ensemble", "harmony", "instrument", "listening", "orchestra", "performing", "recording", "rehearsal", "saxophone", "symphony", "trombone", "trumpet", "woodwind"],
        10: ["instrument", "percussion", "production", "saxophone", "synthesizer", "arrangement", "background", "collection", "composing", "conducting", "electronic", "instrument", "melodious", "orchestra", "percussion", "performing", "production", "recording", "saxophone", "soundtrack", "symphony", "technique", "trombone", "vibraphone", "woodwinds"]
    },
    "brands": {
        3: ["ibm", "bmw", "kfc", "ups", "gap", "amd", "bic", "bmw", "cvs", "dhl", "ebay", "gap", "gmc", "htc", "ibm", "kfc", "lg", "mac", "nbc", "pbs", "rca", "sap", "tnt", "ups", "wwe"],
        4: ["nike", "ford", "dell", "sony", "visa", "acer", "asus", "dell", "fila", "ford", "gucci", "honda", "ikea", "jeep", "lego", "nike", "puma", "rolex", "sony", "uber", "visa", "xbox", "yahoo", "zara", "zoom"],
        5: ["apple", "adobe", "nokia", "pepsi", "xerox", "adidas", "adobe", "apple", "canon", "cisco", "fedex", "google", "honda", "intel", "kodak", "lexus", "nokia", "pepsi", "shell", "tesla", "toyota", "vizio", "xerox", "yahoo", "zeiss"],
        6: ["amazon", "google", "oracle", "paypal", "toyota", "airbnb", "amazon", "burger", "chanel", "disney", "fedex", "google", "hermes", "honda", "lenovo", "nestle", "oracle", "paypal", "prada", "rolex", "subway", "toyota", "virgin", "walmart", "xiaomi"],
        7: ["samsung", "walmart", "youtube", "twitter", "spotify", "adidas", "alibaba", "android", "boeing", "colgate", "comcast", "ferrari", "gillette", "heineken", "huawei", "linkedin", "logitech", "netflix", "nintendo", "samsung", "spotify", "twitter", "walmart", "youtube", "zalando"],
        8: ["facebook", "mercedes", "microsoft", "starbucks", "whatsapp", "alphabet", "amazon", "android", "chrysler", "facebook", "fidelity", "heineken", "infiniti", "linkedin", "logitech", "mercedes", "nintendo", "phillips", "samsung", "snapchat", "spotify", "starbucks", "telegram", "whatsapp", "youtube"],
        9: ["instagram", "mcdonalds", "pinterest", "snapchat", "wordpress", "accenture", "activision", "coca-cola", "discovery", "dropbox", "facebook", "instagram", "mastercard", "mcdonalds", "microsoft", "nintendo", "pinterest", "qualcomm", "salesforce", "samsung", "snapchat", "starbucks", "wordpress", "youtube", "zillow"],
        10: ["volkswagen", "playstation", "mastercard", "coca-cola", "microsoft", "activision", "blackberry", "bloomberg", "coca-cola", "enterprise", "facebook", "instagram", "mastercard", "mcdonalds", "microsoft", "mitsubishi", "nintendo", "playstation", "salesforce", "samsung", "snapchat", "starbucks", "volkswagen", "whatsapp", "wordpress"]
    },
    "history": {
        3: ["war", "era", "age", "law", "map", "act", "ark", "axe", "bow", "era", "gun", "law", "log", "old", "raj", "rex", "tao", "tax", "war", "wax", "yin", "eon", "foe", "ode", "urn"],
        4: ["time", "king", "rome", "date", "past", "army", "book", "city", "date", "epic", "fact", "gold", "hero", "king", "land", "myth", "past", "rome", "rule", "saga", "time", "tomb", "war", "year", "ruin"],
        5: ["event", "queen", "royal", "trade", "world", "armor", "battle", "crown", "egypt", "event", "faith", "greek", "kings", "medal", "peace", "queen", "reign", "roman", "royal", "ruler", "sword", "trade", "tribe", "world", "years"],
        6: ["battle", "empire", "nation", "period", "treaty", "ancient", "battle", "castle", "empire", "events", "legacy", "leader", "legion", "nation", "period", "plague", "record", "revolt", "romans", "treaty", "tribal", "viking", "weapon", "scroll", "throne"],
        7: ["ancient", "dynasty", "kingdom", "monarch", "warfare", "ancient", "archive", "aztecs", "battle", "century", "crusade", "dynasty", "empire", "history", "kingdom", "legacy", "mayans", "monarch", "persian", "pharaoh", "romans", "slavery", "vikings", "warfare", "warrior"],
        8: ["medieval", "monarchy", "republic", "timeline", "warrior", "alliance", "ancestor", "artifact", "calendar", "conquest", "crusader", "dynasty", "egyptian", "emperor", "heritage", "historic", "kingdom", "medieval", "monarchy", "pharaoh", "republic", "timeline", "warrior", "weapons", "writing"],
        9: ["artifacts", "byzantine", "chronicle", "conquest", "discovery", "ancestor", "antiquity", "artifacts", "byzantine", "calendar", "chronicle", "conquest", "crusaders", "discovery", "document", "dynasty", "egyptian", "heritage", "historian", "imperial", "medieval", "monarchy", "timeline", "tradition", "warriors"],
        10: ["archaeology", "civilization", "colonialism", "historical", "revolution", "antiquities", "archaeology", "byzantine", "chronology", "civilization", "colonialism", "crusaders", "discovery", "documentary", "expedition", "historical", "imperialism", "industrial", "monarchy", "prehistoric", "revolution", "settlement", "tradition", "victorian", "warfare"]
    },
    "random": {
        3: ["any", "mix", "odd", "try", "new", "all", "bet", "cut", "die", "fog", "gap", "hex", "ink", "jot", "key", "lot", "nix", "opt", "pin", "qed", "raw", "sum", "try", "urn", "var"],
        4: ["luck", "pick", "roll", "spin", "wild", "auto", "blur", "card", "dice", "edge", "flip", "game", "haze", "idea", "jump", "luck", "maze", "odds", "pick", "quiz", "risk", "seed", "void", "whim", "zero"],
        5: ["chaos", "guess", "lucky", "quirky", "twist", "blend", "chaos", "crazy", "dream", "flash", "guess", "hunch", "lucky", "magic", "novel", "quirk", "rapid", "spark", "swift", "twist", "vague", "weird", "yield", "zesty"],
        6: ["chance", "random", "sudden", "unique", "varied", "chance", "chaos", "custom", "divine", "enigma", "fickle", "hybrid", "impact", "jumble", "lottery", "mystic", "random", "riddle", "sudden", "switch", "unique", "varied", "wonder", "zigzag", "zinger"],
        7: ["fortune", "mystery", "random", "shuffle", "strange", "amazing", "bizarre", "chance", "dynamic", "entropy", "fortune", "impulse", "lottery", "mystery", "obscure", "quantum", "radical", "shuffle", "strange", "surreal", "unknown", "variant", "wonder", "zigzag", "zinger"],
        8: ["accident", "fortune", "mystery", "peculiar", "surprise", "accident", "arbitrary", "chaotic", "fortune", "haphazard", "impulse", "irregular", "lottery", "mystery", "peculiar", "quantum", "random", "scattered", "sporadic", "surprise", "uncertain", "variable", "wandering", "whimsical", "zigzagged"],
        9: ["arbitrary", "eccentric", "fortuitous", "irregular", "spontaneous", "accidental", "arbitrary", "eccentric", "fortuitous", "haphazard", "irregular", "mysterious", "peculiar", "quantum", "randomized", "scattered", "sporadic", "stochastic", "surprising", "uncertain", "unexpected", "unpredicted", "variable", "wandering", "whimsical"],
        10: ["accidental", "mysterious", "randomized", "spontaneous", "unexpected", "accidental", "arbitrary", "capricious", "eccentric", "fortuitous", "haphazard", "impulsive", "irregular", "mysterious", "peculiar", "quantum", "randomized", "scattered", "spontaneous", "stochastic", "surprising", "uncertain", "unexpected", "variable", "whimsical"]
    },
    "animals": {
        3: ["ant", "bee", "cat", "dog", "owl", "bat", "cow", "elk", "fox", "hen", "jay", "koi", "pig", "rat", "yak", "ape", "bug", "cub", "doe", "emu", "pup", "hog", "kit", "ram", "zoo"],
        4: ["bear", "deer", "frog", "lion", "wolf", "apes", "bird", "calf", "duck", "fish", "goat", "hare", "kiwi", "lynx", "mole", "newt", "orca", "puma", "seal", "toad", "vole", "wasp", "yeti", "zebu", "boar"],
        5: ["camel", "eagle", "horse", "koala", "zebra", "bison", "chimp", "dingo", "ferret", "gecko", "hyena", "iguana", "lemur", "moose", "otter", "panda", "quail", "rhino", "shark", "tiger", "viper", "whale", "xerus", "yabby", "cobra"],
        6: ["jaguar", "monkey", "panda", "rabbit", "turtle", "alpaca", "badger", "cheetah", "donkey", "falcon", "gibbon", "jackal", "impala", "koala", "kudu", "lizard", "marten", "osprey", "parrot", "quokka", "salmon", "toucan", "walrus", "weasel", "python"],
        7: ["dolphin", "penguin", "octopus", "giraffe", "hamster", "antelope", "buffalo", "caracal", "dugong", "echidna", "flamingo", "gazelle", "hedgehog", "iguana", "lioness", "meerkat", "ocelot", "panther", "raccoon", "seagull", "tapir", "vulture", "wallaby", "wombat", "zebra"],
        8: ["elephant", "gorilla", "kangaroo", "squirrel", "butterfly", "aardvark", "antelope", "baboon", "caribou", "duckbill", "gazelle", "hamster", "leopard", "manatee", "ocelot", "penguin", "platypus", "seagull", "tortoise", "vulture", "walrus", "weasel", "wildcat", "wildebeest", "wolverine"],
        9: ["crocodile", "hedgehog", "jellyfish", "porcupine", "seahorse", "alligator", "anteater", "armadillo", "barracuda", "chameleon", "dalmatian", "echidna", "flamingo", "gorilla", "lionfish", "mongoose", "narwhal", "octopus", "penguin", "reindeer", "scorpion", "stingray", "tortoise", "wallaby", "wildebeest"],
        10: ["hippopotamus", "rhinoceros", "chimpanzee", "orangutan", "hummingbird", "alligator", "barracuda", "butterfly", "crocodile", "dragonfly", "elephant", "flamingo", "gazelle", "hamster", "kangaroo", "leopard", "mongoose", "narwhal", "orangutan", "penguin", "porcupine", "rhinoceros", "seahorse", "tortoise", "wolverine"]
    },
    "food": {
        3: ["pie", "ham", "egg", "tea", "jam", "bun", "dip", "fig", "pea", "nut", "oil", "rye", "soy", "yam", "ale", "cod", "eel", "fry", "gin", "ham", "jus", "kim", "mac", "nib", "poi"],
        4: ["cake", "rice", "soup", "fish", "meat", "bean", "beef", "corn", "duck", "eggs", "flan", "grape", "herb", "kale", "lime", "mint", "nuts", "oats", "pear", "rice", "sage", "tuna", "wine", "yams", "zest"],
        5: ["pizza", "pasta", "bread", "salad", "sushi", "apple", "bacon", "candy", "dates", "flour", "grape", "honey", "juice", "kiwis", "lemon", "mango", "olive", "peach", "quail", "salad", "toast", "wheat", "yogurt", "berry", "curry"],
        6: ["burger", "cookie", "cheese", "coffee", "butter", "banana", "carrot", "celery", "donut", "garlic", "ginger", "herbs", "jelly", "lentil", "mango", "orange", "papaya", "pepper", "quinoa", "radish", "salmon", "tomato", "waffle", "yogurt", "ziti"],
        7: ["chicken", "pancake", "waffle", "yogurt", "icecream", "almond", "apricot", "avocado", "biscuit", "cashew", "coconut", "custard", "eggroll", "falafel", "granola", "hazelnut", "hotdog", "lasagna", "muffin", "noodle", "oatmeal", "popcorn", "pretzel", "ravioli", "sausage"],
        8: ["sandwich", "lasagna", "popcorn", "broccoli", "mushroom", "artichoke", "asparagus", "blueberry", "cabbage", "cucumber", "eggplant", "focaccia", "guacamole", "hummus", "jalapeno", "ketchup", "licorice", "macaroni", "mustard", "pancake", "pineapple", "porridge", "spaghetti", "tortilla", "zucchini"],
        9: ["chocolate", "blueberry", "pineapple", "hamburger", "asparagus", "artichoke", "blackberry", "cranberry", "croissant", "dumpling", "edamame", "grapefruit", "kiwifruit", "lemonade", "marmalade", "meatball", "milkshake", "mushroom", "parmesan", "pepperoni", "raspberry", "smoothie", "tangerine", "vegetable", "watercress"],
        10: ["strawberry", "watermelon", "grapefruit", "blackberry", "cauliflower", "applesauce", "blueberry", "cheesecake", "clementine", "cranberry", "gingerbread", "gooseberry", "honeydew", "lemongrass", "mangostein", "mulberry", "persimmon", "pomegranate", "pumpkin pie", "raspberry", "tangerine", "vanilla", "watercress", "watermelon", "yellowfin"]
    },
    "places": {
        3: ["bay", "sea", "sky", "zoo", "spa", "arc", "bar", "bay", "dam", "den", "gym", "hub", "inn", "lab", "map", "mew", "oar", "pub", "row", "spa", "tor", "via", "way", "yam", "zen"],
        4: ["city", "park", "lake", "home", "mall", "arch", "bank", "base", "cafe", "cave", "dock", "dome", "farm", "gate", "hall", "hill", "isle", "jail", "lake", "mine", "park", "pier", "port", "reef", "shop"],
        5: ["beach", "hotel", "house", "store", "plaza", "abbey", "arena", "beach", "cabin", "canal", "cliff", "coast", "court", "cove", "creek", "depot", "docks", "field", "grove", "hotel", "house", "lodge", "manor", "oasis", "plaza"],
        6: ["garden", "museum", "school", "temple", "castle", "arcade", "bakery", "bridge", "bunker", "campus", "casino", "center", "chapel", "church", "clinic", "colony", "forest", "garage", "harbor", "hostel", "market", "office", "palace", "resort", "shrine"],
        7: ["library", "airport", "college", "theater", "stadium", "academy", "arcade", "barracks", "brewery", "campus", "castle", "cavern", "chateau", "college", "factory", "gallery", "garden", "harbor", "highway", "hospice", "mansion", "marina", "mosque", "orchard", "palace"],
        8: ["hospital", "mountain", "building", "seashore", "vineyard", "airport", "aquarium", "ballpark", "barracks", "bookstore", "brewery", "building", "cafeteria", "cathedral", "cemetery", "citadel", "coliseum", "compound", "corridor", "courtyard", "district", "driveway", "embassy", "factory", "fountain"],
        9: ["apartment", "cathedral", "classroom", "courtyard", "sanctuary", "aerodrome", "amphitheater", "aquarium", "arboretum", "auditorium", "ballroom", "boulevard", "bungalow", "cafeteria", "cathedral", "cemetery", "citadel", "classroom", "clubhouse", "courthouse", "dormitory", "firestation", "gymnasium", "laboratory", "lighthouse"],
        10: ["restaurant", "university", "lighthouse", "playground", "waterfront", "aerodrome", "amphitheater", "apartment", "auditorium", "boardwalk", "bookstore", "boulevard", "courthouse", "department", "dormitory", "firestation", "greenhouse", "gymnasium", "hospital", "laboratory", "lighthouse", "monastery", "observatory", "planetarium", "waterfront"]
    },
    "science": {
        3: ["dna", "rna", "ion", "gas", "ohm", "air", "amp", "atom", "bit", "cal", "dye", "eon", "fmr", "gel", "hex", "ion", "kev", "lab", "mag", "nmr", "ohm", "psi", "rad", "sin", "tau"],
        4: ["atom", "cell", "gene", "mass", "volt", "acid", "apex", "axis", "base", "beam", "bond", "core", "data", "echo", "flux", "fuse", "gram", "heat", "ion", "joule", "kelvin", "lens", "mole", "node", "wave"],
        5: ["laser", "quark", "helix", "prism", "tesla", "alpha", "amino", "angle", "atom", "boson", "cycle", "delta", "field", "fluid", "force", "gamma", "graph", "joule", "light", "molar", "nexus", "orbit", "phase", "pulse", "qubit"],
        6: ["photon", "plasma", "proton", "enzyme", "matrix", "action", "aether", "allele", "atomic", "binary", "carbon", "charge", "cosmic", "crystal", "energy", "factor", "fusion", "genome", "gravity", "magnet", "matter", "neuron", "oxygen", "photon", "plasma"],
        7: ["neutron", "isotope", "magnet", "nucleus", "quantum", "algebra", "atomic", "battery", "biology", "calcium", "channel", "circuit", "density", "ecology", "electron", "element", "entropy", "formula", "gravity", "helium", "impulse", "inertia", "kinetic", "magnet", "nucleus"],
        8: ["electron", "molecule", "particle", "catalyst", "chemical", "absolute", "acoustic", "ammonia", "analysis", "bacteria", "balance", "battery", "calculus", "chemical", "compound", "density", "diameter", "element", "entropy", "equation", "friction", "function", "gradient", "magnetic", "momentum"],
        9: ["radiation", "astronomy", "evolution", "chemistry", "physicist", "algorithm", "amplitude", "atmosphere", "bacteria", "biosphere", "catalyst", "chemistry", "chromosome", "collision", "combustion", "conductor", "cosmology", "diffusion", "dimension", "elasticity", "frequency", "generator", "gravitate", "magnetic", "molecular"],
        10: ["microscope", "experiment", "laboratory", "technology", "hypothesis", "absorption", "acoustics", "algorithm", "atmosphere", "barometer", "biosphere", "calculator", "chromosome", "combustion", "conductor", "coordinate", "diffusion", "dispersion", "elasticity", "electricity", "experiment", "frequency", "gravitation", "hypothesis", "laboratory"]
    },
    "tech": {
        3: ["app", "cpu", "ram", "usb", "lan", "api", "bit", "bug", "css", "dev", "dns", "ftp", "git", "gui", "hub", "ide", "ios", "key", "log", "mac", "net", "php", "sql", "tag", "xml"],
        4: ["code", "data", "wifi", "byte", "html", "ajax", "bash", "beta", "blog", "boot", "byte", "chat", "chip", "code", "data", "disk", "file", "font", "host", "java", "link", "mail", "node", "port", "ruby"],
        5: ["linux", "cloud", "pixel", "cache", "robot", "admin", "array", "audio", "batch", "cache", "class", "cloud", "codec", "debug", "email", "flash", "frame", "image", "index", "linux", "macro", "media", "mysql", "pixel", "query"],
        6: ["python", "server", "docker", "github", "nodejs", "apache", "backup", "binary", "buffer", "client", "cookie", "cursor", "debian", "docker", "domain", "driver", "filter", "folder", "format", "github", "kernel", "layout", "method", "module", "nodejs"],
        7: ["android", "network", "bitcoin", "mongodb", "devops", "adapter", "android", "archive", "backend", "browser", "channel", "compile", "console", "control", "desktop", "devops", "display", "encrypt", "firewall", "gateway", "hosting", "network", "package", "program", "routing"],
        8: ["database", "software", "ethernet", "protocol", "frontend", "abstract", "assembly", "backbone", "compiler", "computer", "database", "ethernet", "firewall", "frontend", "function", "hardware", "internet", "keyboard", "malware", "monitor", "network", "platform", "protocol", "software", "terminal"],
        9: ["algorithm", "framework", "interface", "compiler", "container", "analytics", "antivirus", "bandwidth", "bootstrap", "broadband", "component", "computer", "container", "database", "developer", "directory", "ethernet", "extension", "firewall", "framework", "interface", "keyboard", "localhost", "mainframe", "processor"],
        10: ["javascript", "kubernetes", "blockchain", "middleware", "encryption", "algorithm", "apache", "artificial", "blockchain", "bootstrap", "collection", "compiler", "container", "controller", "database", "deployment", "developer", "encryption", "framework", "javascript", "kubernetes", "middleware", "networking", "processing", "technology"]
    },
    "sports": {
        3: ["run", "ski", "box", "gym", "jog", "aim", "bat", "bow", "cup", "fan", "fit", "hit", "lap", "net", "par", "ref", "run", "tag", "win", "ace", "dip", "hop", "jab", "pin", "tee"],
        4: ["ball", "golf", "swim", "race", "team", "base", "bike", "bowl", "dive", "game", "goal", "jump", "kick", "lift", "pass", "play", "rush", "shot", "toss", "win", "dash", "flip", "grip", "pace", "spin"],
        5: ["sport", "track", "rugby", "skate", "score", "climb", "fence", "guard", "spike", "court", "cycle", "serve", "pitch", "fight", "medal", "match", "block", "swing", "throw", "drill", "field", "rally", "slide", "speed", "vault"],
        6: ["soccer", "tennis", "boxing", "hockey", "karate", "strike", "archer", "tackle", "combat", "course", "defend", "sprint", "fitness", "league", "player", "racing", "sports", "volley", "batter", "dangle", "hurdle", "paddle", "runner", "stroke", "triple"],
        7: ["cricket", "running", "cycling", "fitness", "skating", "athlete", "batting", "bowling", "scoring", "defense", "serving", "jogging", "jumping", "offense", "pitcher", "referee", "workout", "balance", "dribble", "endzone", "fielder", "gymnast", "rebound", "sprints", "tactics"],
        8: ["baseball", "football", "swimming", "athletics", "training", "aerobics", "archery", "athletic", "bowling", "climbing", "coaching", "curling", "exercise", "handball", "olympics", "practice", "skating", "sparring", "spinning", "sprinter", "strength", "throwing", "triathlon", "wrestler", "yoga"],
        9: ["basketball", "gymnastics", "wrestling", "volleyball", "badminton", "athletics", "bicycling", "boxing", "coaching", "cricket", "dodgeball", "exercise", "football", "handball", "hockey", "lacrosse", "olympics", "softball", "swimming", "acrobatic", "endurance", "kickboxer", "marathon", "pentathlon", "taekwondo"],
        10: ["volleyball", "basketball", "gymnastics", "waterpolo", "pickleball", "athletics", "badminton", "bicycling", "cheerleader", "competition", "dodgeball", "exercising", "handball", "pickleball", "powerlifting", "racquetball", "skateboard", "swimming", "taekwondo", "trampoline", "triathlon", "weightlift", "wrestling", "decathlon", "pentathlon"]
    }
}

# Add aliases for similar categories
CATEGORY_ALIASES = {
    "exercise": "sports",
    "fitness": "sports",
    "games": "sports",
    "olympic": "sports"
}

def get_fallback_word(word_length: int, subject: str) -> Optional[str]:
    """
    Get a random word from the fallback dictionary matching the given length and subject.
    Falls back to "general" category if the subject is not found.
    Avoids using template words too frequently.
    """
    logger = logging.getLogger(__name__)
    
    # Normalize subject to lowercase
    subject = subject.lower()
    subject = CATEGORY_ALIASES.get(subject, subject)
    
    # Get words matching the length from both the specified subject and general category
    subject_words = []
    if subject in FALLBACK_WORDS:
        subject_words = FALLBACK_WORDS[subject].get(word_length, [])
    general_words = FALLBACK_WORDS["general"].get(word_length, [])
    
    # Define template words to avoid
    template_words = {"table", "music", "phone", "light"}  # Common template words
    available_words = []
    
    # First try subject-specific words, excluding template words
    if subject_words:
        non_template_words = [w for w in subject_words if w not in template_words]
        if non_template_words:
            available_words.extend(non_template_words)
    
    # If we don't have enough words, add general words (excluding template words)
    if len(available_words) < 5:
        non_template_general = [w for w in general_words if w not in template_words]
        available_words.extend(non_template_general)
    
    # Only if we have no other options, include template words
    if not available_words:
        logger.warning("No non-template words available, falling back to template words")
        available_words = subject_words + general_words
    
    if not available_words:
        logger.error(f"No words available for length {word_length} and subject {subject}")
        return None
        
    selected_word = random.choice(available_words)
    logger.info(f"Selected word: {selected_word} from pool of {len(available_words)} words")
    return selected_word 