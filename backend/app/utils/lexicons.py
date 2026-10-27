"""
lexicons.py

Hand-curated linguistic resources used by the rule-based / hybrid NLP layer.

These are intentionally transparent (as opposed to a black-box model) so that
every prediction the pipeline makes can be traced back to a concrete signal.
This module is the single source of truth for:

  - SENTIMENT_LEXICON   : word -> polarity weight in [-1, 1]
  - INTENSIFIERS        : words that scale the polarity of the following word
  - NEGATIONS           : words that flip the polarity of the following words
  - EMOTION_LEXICON     : word -> emotion label (Joy, Love, Anger, Sadness, Fear, Surprise)
  - DOMAIN_ASPECTS      : domain -> {aspect_label: [surface forms / synonyms]}
  - COMPLAINT_TERMS     : words/phrases that signal a complaint, weighted by severity
  - NEGATION_WINDOW     : how many tokens a negation affects
"""

# ---------------------------------------------------------------------------
# Sentiment polarity lexicon (compact VADER-inspired custom lexicon)
# ---------------------------------------------------------------------------
SENTIMENT_LEXICON = {
    # strong positive
    "excellent": 1.0, "amazing": 1.0, "fantastic": 1.0, "outstanding": 1.0,
    "perfect": 1.0, "love": 0.9, "loved": 0.9, "wonderful": 0.9, "great": 0.8,
    "awesome": 0.9, "brilliant": 0.9, "superb": 0.9, "impressive": 0.8,
    "delightful": 0.8, "flawless": 0.9, "beautiful": 0.7, "premium": 0.6,
    "fast": 0.5, "smooth": 0.5, "reliable": 0.6, "comfortable": 0.6,
    "durable": 0.6, "responsive": 0.5, "friendly": 0.6, "helpful": 0.6,
    "affordable": 0.5, "worth": 0.4, "recommend": 0.7, "happy": 0.7,
    "best": 0.8,
    "satisfied": 0.7, "pleased": 0.6, "good": 0.6, "nice": 0.5,
    "clean": 0.5, "quick": 0.4, "sturdy": 0.5, "value": 0.3, "crisp": 0.5,
    "vibrant": 0.5, "seamless": 0.6, "efficient": 0.5, "spacious": 0.4,
    # mild positive
    "fine": 0.3, "decent": 0.3, "okay": 0.15, "ok": 0.15, "adequate": 0.2,
    # strong negative
    "terrible": -1.0, "horrible": -1.0, "awful": -1.0, "worst": -1.0,
    "useless": -0.9, "disgusting": -0.9, "unacceptable": -0.9,
    "broken": -0.8, "defective": -0.9, "faulty": -0.8, "poor": -0.7,
    "bad": -0.6, "disappointing": -0.7, "disappointed": -0.7, "waste": -0.8,
    "scam": -1.0, "fraud": -1.0, "rude": -0.7, "slow": -0.5, "late": -0.5,
    "delayed": -0.5, "cheap": -0.4, "flimsy": -0.6, "noisy": -0.4,
    "uncomfortable": -0.6, "damaged": -0.8, "cracked": -0.8, "leaking": -0.7,
    "overpriced": -0.6, "expensive": -0.3, "buggy": -0.7, "laggy": -0.6,
    "unresponsive": -0.7, "dirty": -0.6, "stale": -0.6, "cold": -0.3,
    "burnt": -0.6, "bland": -0.4, "rotten": -0.9, "unhygienic": -0.9,
    "misleading": -0.6, "annoying": -0.5, "frustrating": -0.7,
    "drains": -0.5, "drained": -0.5, "crashes": -0.7, "crashed": -0.7,
    "crashing": -0.7,
    "hangs": -0.5, "lags": -0.5, "malfunctioning": -0.8, "unresponsively": -0.5,
    "never": -0.3, "wrong": -0.6, "missing": -0.5, "ignored": -0.6,
    "unresolved": -0.6, "hate": -0.9, "hated": -0.9, "regret": -0.7,
    # mild negative
    "mediocre": -0.4, "average": -0.1, "meh": -0.3, "lacking": -0.4,
    "unhelpful": -0.6, "forever": -0.3, "unresponsive": -0.7, "ignored": -0.6,
    "unfriendly": -0.5, "confusing": -0.4, "outdated": -0.4, "unreliable": -0.6,
    "loud": -0.3, "tasteless": -0.6, "stained": -0.5, "torn": -0.6,
    "unprofessional": -0.7, "incompetent": -0.7, "careless": -0.6,
}

INTENSIFIERS = {
    "very": 1.4, "extremely": 1.6, "really": 1.3, "so": 1.2, "too": 1.2,
    "incredibly": 1.5, "absolutely": 1.5, "totally": 1.4, "completely": 1.4,
    "highly": 1.3, "super": 1.3, "quite": 1.15, "slightly": 0.6, "somewhat": 0.7,
    "a bit": 0.6, "barely": 0.5,
}

NEGATIONS = {
    "not", "no", "never", "n't", "cannot", "can't", "won't", "don't",
    "doesn't", "didn't", "isn't", "wasn't", "aren't", "weren't", "without",
    "hardly", "barely",
}

NEGATION_WINDOW = 3  # number of following tokens a negation can flip

# ---------------------------------------------------------------------------
# Emotion lexicon — compact NRC-inspired mapping
# ---------------------------------------------------------------------------
EMOTION_LEXICON = {
    "Joy": [
        "happy", "joy", "delighted", "pleased", "glad", "cheerful", "great",
        "excellent", "fantastic", "wonderful", "satisfied", "smile", "fun",
        "enjoyed", "enjoy", "amazing", "awesome", "perfect", "impressed",
    ],
    "Love": [
        "love", "loved", "loving", "adore", "adorable", "favorite", "favourite",
        "obsessed", "beautiful", "gorgeous", "charming",
    ],
    "Anger": [
        "angry", "furious", "annoyed", "annoying", "rude", "unacceptable",
        "outrageous", "infuriating", "frustrated", "frustrating", "mad",
        "hate", "hated", "disrespectful", "ignored", "scam", "fraud",
    ],
    "Sadness": [
        "sad", "disappointed", "disappointing", "unhappy", "regret",
        "heartbroken", "upset", "letdown", "miserable", "sorry", "unfortunate",
    ],
    "Fear": [
        "worried", "concerned", "afraid", "scared", "nervous", "unsafe",
        "risky", "anxious", "hazard", "dangerous", "suspicious",
    ],
    "Surprise": [
        "surprised", "shocked", "unexpected", "unbelievable", "wow",
        "surprisingly", "astonished", "sudden",
    ],
}

# ---------------------------------------------------------------------------
# Domain-aware aspect vocabulary
#   Maps a canonical aspect label -> list of surface forms / synonyms
# ---------------------------------------------------------------------------

DOMAIN_ASPECTS = {

    # =======================================================================
    # ELECTRONICS
    # =======================================================================

    "electronics": {

        "Battery": [
            "battery",
            "battery life",
            "backup",
            "battery backup",
            "charge",
            "charging",
            "charger",
            "power",
            "power backup",
            "drain",
            "draining",
        ],

        "Camera": [
            "camera",
            "photo",
            "photos",
            "picture",
            "pictures",
            "picture quality",
            "image quality",
            "lens",
            "selfie",
            "selfie camera",
            "front camera",
            "rear camera",
            "video quality",
        ],

        "Display": [
            "display",
            "screen",
            "resolution",
            "brightness",
            "panel",
            "touchscreen",
            "touch screen",
            "colors",
            "colours",
            "refresh rate",
        ],

        "Performance": [
            "performance",
            "speed",
            "processor",
            "cpu",
            "gpu",
            "ram",
            "lag",
            "lags",
            "lagging",
            "slow",
            "fps",
            "gaming",
            "multitasking",
            "response time",
        ],

        "Audio": [
            "audio",
            "sound",
            "sound quality",
            "speaker",
            "speakers",
            "volume",
            "microphone",
            "mic",
            "earpiece",
            "bass",
        ],

        "Connectivity": [
            "wifi",
            "wi-fi",
            "internet",
            "network",
            "connection",
            "connectivity",
            "bluetooth",
            "signal",
            "mobile network",
            "5g",
            "4g",
            "nfc",
        ],

        "Design": [
            "design",
            "look",
            "looks",
            "appearance",
            "style",
            "finish",
            "aesthetics",
            "color",
            "colour",
        ],

        "Build Quality": [
            "build quality",
            "build",
            "material",
            "body",
            "frame",
            "sturdiness",
            "sturdy",
            "durability",
            "durable",
            "hinge",
        ],

        "Software": [
            "software",
            "app",
            "apps",
            "ui",
            "interface",
            "update",
            "updates",
            "os",
            "operating system",
            "firmware",
            "bug",
            "bugs",
        ],

        "Storage": [
            "storage",
            "memory",
            "disk space",
            "internal storage",
            "ssd",
            "hard drive",
        ],

        "Heating": [
            "heating",
            "heat",
            "hot",
            "overheating",
            "temperature",
        ],

        "Features": [
            "feature",
            "features",
            "function",
            "functions",
            "functionality",
        ],

        "Ease of Use": [
            "easy to use",
            "ease of use",
            "user friendly",
            "user-friendly",
            "difficult to use",
            "setup",
            "installation",
        ],

        "Price": [
            "price",
            "cost",
            "pricing",
            "value for money",
            "value",
            "expensive",
            "cheap",
            "affordable",
        ],
    },


    # =======================================================================
    # E-COMMERCE
    # =======================================================================

    "ecommerce": {

        "Product Quality": [
            "product quality",
            "quality",
            "material",
            "build quality",
            "build",
            "durable",
            "durability",
            "sturdy",
            "sturdiness",
            "finish",
            "condition",
        ],

        "Delivery": [
            "delivery",
            "shipping",
            "courier",
            "shipment",
            "dispatch",
            "arrived",
            "arrival",
            "delivery time",
            "shipping time",
            "delivery speed",
        ],

        "Packaging": [
            "packaging",
            "package",
            "packing",
            "box",
            "wrapping",
            "parcel",
        ],

        "Price": [
            "price",
            "cost",
            "pricing",
            "value for money",
            "value",
            "expensive",
            "cheap",
            "affordable",
            "discount",
            "offer",
        ],

        "Customer Support": [
            "customer support",
            "support",
            "customer service",
            "helpline",
            "agent",
            "representative",
            "support team",
            "customer care",
        ],

        "Return": [
            "return",
            "returned",
            "return policy",
            "exchange",
            "replacement",
            "replace",
        ],

        "Refund": [
            "refund",
            "refunded",
            "money back",
            "reimbursement",
            "refund process",
        ],

        "Payment": [
            "payment",
            "transaction",
            "card",
            "credit card",
            "debit card",
            "upi",
            "cash on delivery",
            "cod",
            "payment gateway",
            "charged",
        ],

        "Website/App": [
            "website",
            "site",
            "app",
            "application",
            "interface",
            "checkout",
            "cart",
            "shopping cart",
        ],

        "Product Availability": [
            "availability",
            "available",
            "unavailable",
            "stock",
            "out of stock",
            "in stock",
            "inventory",
        ],

        "Product Description": [
            "description",
            "product description",
            "specification",
            "specifications",
            "details",
            "product details",
        ],

        "Order": [
            "order",
            "ordering",
            "order process",
            "order status",
            "order tracking",
            "tracking",
        ],

        "Seller": [
            "seller",
            "vendor",
            "merchant",
        ],
    },


    # =======================================================================
    # RESTAURANT
    # =======================================================================

    "restaurant": {

        "Food": [
            "food",
            "dish",
            "dishes",
            "meal",
            "meals",
            "menu",
            "cuisine",
        ],

        "Taste": [
            "taste",
            "tasty",
            "delicious",
            "flavor",
            "flavour",
            "spicy",
            "bland",
            "salty",
            "sweet",
            "sour",
            "fresh",
            "stale",
        ],

        "Service": [
            "service",
            "serving",
            "waiter",
            "waitress",
            "server",
            "service time",
            "waiting time",
            "wait time",
        ],

        "Staff": [
            "staff",
            "employee",
            "employees",
            "manager",
            "waiter",
            "waitress",
            "server",
            "team",
        ],

        "Price": [
            "price",
            "cost",
            "expensive",
            "cheap",
            "affordable",
            "value for money",
            "bill",
            "billing",
        ],

        "Ambience": [
            "ambience",
            "ambiance",
            "atmosphere",
            "music",
            "decor",
            "decoration",
            "interior",
            "lighting",
            "environment",
        ],

        "Cleanliness": [
            "cleanliness",
            "clean",
            "dirty",
            "hygiene",
            "hygienic",
            "unhygienic",
            "sanitation",
        ],

        "Seating": [
            "seat",
            "seats",
            "seating",
            "table",
            "tables",
            "chair",
            "chairs",
        ],

        "Portion Size": [
            "portion",
            "portion size",
            "quantity",
            "serving size",
        ],

        "Food Temperature": [
            "hot food",
            "cold food",
            "food temperature",
            "temperature",
        ],

        "Waiting Time": [
            "waiting",
            "waiting time",
            "wait time",
            "delay",
            "delayed",
        ],

        "Reservation": [
            "reservation",
            "booking",
            "table booking",
            "booked",
        ],

        "Delivery": [
            "delivery",
            "food delivery",
            "delivered",
            "delivery time",
        ],

        "Packaging": [
            "packaging",
            "package",
            "packing",
            "container",
        ],
    },


    # =======================================================================
    # HOTEL
    # =======================================================================

    "hotel": {

        "Room": [
            "room",
            "rooms",
            "bedroom",
            "suite",
            "furniture",
            "bathroom",
            "washroom",
            "toilet",
            "shower",
            "hot water",
            "water",
        ],

        "Cleanliness": [
            "cleanliness",
            "clean",
            "cleaned",
            "cleaning",
            "dirty",
            "dirt",
            "hygiene",
            "hygienic",
            "unhygienic",
            "housekeeping",
            "dust",
            "dusty",
            "stain",
            "stained",
            "smell",
            "smelly",
            "odor",
            "odour",
        ],

        "Staff": [
            "staff",
            "reception",
            "receptionist",
            "concierge",
            "employee",
            "employees",
            "manager",
            "hotel staff",
            "team",
        ],

        "Service": [
            "service",
            "room service",
            "customer service",
            "front desk",
            "check-in",
            "check in",
            "check-out",
            "check out",
            "response",
            "assistance",
        ],

        "Location": [
            "location",
            "area",
            "neighborhood",
            "neighbourhood",
            "access",
            "nearby",
            "distance",
            "airport",
            "station",
            "city center",
            "city centre",
        ],

        "Food": [
            "food",
            "breakfast",
            "lunch",
            "dinner",
            "meal",
            "restaurant",
            "buffet",
            "dining",
            "menu",
            "food quality",
        ],

        "Taste": [
            "taste",
            "tasty",
            "delicious",
            "flavor",
            "flavour",
            "bland",
            "fresh",
            "stale",
        ],

        "Comfort": [
            "comfort",
            "comfortable",
            "uncomfortable",
            "bed comfort",
            "mattress",
            "pillow",
            "pillows",
            "blanket",
        ],

        "Connection": [
            "wifi",
            "wi-fi",
            "internet",
            "network",
            "connection",
            "connectivity",
            "signal",
        ],

        "Facilities": [
            "facility",
            "facilities",
            "amenity",
            "amenities",
            "gym",
            "fitness center",
            "fitness centre",
            "spa",
            "pool",
            "swimming pool",
            "lounge",
        ],

        "Air Conditioning": [
            "air conditioning",
            "air conditioner",
            "ac",
            "a/c",
            "cooling",
            "heater",
            "heating",
        ],

        "Noise": [
            "noise",
            "noisy",
            "loud",
            "sound",
            "quiet",
            "peaceful",
        ],

        "Safety": [
            "safety",
            "safe",
            "unsafe",
            "security",
            "secure",
            "lock",
            "door lock",
        ],

        "Price": [
            "price",
            "cost",
            "rate",
            "room rate",
            "expensive",
            "cheap",
            "affordable",
            "value for money",
            "value",
        ],

        "Booking": [
            "booking",
            "reservation",
            "reservation process",
            "booked",
            "room booking",
        ],

        "Payment": [
            "payment",
            "bill",
            "billing",
            "charged",
            "charge",
            "transaction",
        ],

        "Parking": [
            "parking",
            "car park",
            "parking space",
            "valet",
        ],

        "View": [
            "view",
            "sea view",
            "city view",
            "mountain view",
            "balcony",
        ],

        "Experience": [
            "experience",
            "stay",
            "overall experience",
            "overall stay",
        ],
    },


    # =======================================================================
    # TRAVEL
    # =======================================================================

    "travel": {

        "Booking": [
            "booking",
            "reservation",
            "ticket",
            "tickets",
            "itinerary",
            "booked",
        ],

        "Staff": [
            "staff",
            "crew",
            "agent",
            "guide",
            "employee",
        ],

        "Price": [
            "price",
            "cost",
            "fare",
            "expensive",
            "cheap",
            "affordable",
            "value for money",
        ],

        "Punctuality": [
            "delay",
            "delayed",
            "late",
            "on time",
            "punctual",
            "punctuality",
            "schedule",
        ],

        "Comfort": [
            "comfort",
            "comfortable",
            "uncomfortable",
            "legroom",
            "seat",
            "seating",
        ],

        "Support": [
            "support",
            "customer service",
            "customer support",
            "helpline",
            "agent",
        ],

        "Journey": [
            "journey",
            "trip",
            "travel",
            "ride",
            "flight",
        ],

        "Luggage": [
            "luggage",
            "baggage",
            "bag",
            "bags",
            "suitcase",
        ],

        "Safety": [
            "safety",
            "safe",
            "unsafe",
            "security",
        ],

        "Cleanliness": [
            "cleanliness",
            "clean",
            "dirty",
            "hygiene",
        ],

        "Food": [
            "food",
            "meal",
            "snack",
            "drink",
            "beverage",
        ],

        "Cancellation": [
            "cancellation",
            "cancelled",
            "canceled",
            "cancel",
        ],

        "Refund": [
            "refund",
            "refunded",
            "money back",
            "reimbursement",
        ],
    },


    # =======================================================================
    # GENERIC / UNKNOWN DOMAIN
    # =======================================================================

    "other": {

        "Quality": [
            "quality",
            "build quality",
            "build",
            "material",
            "condition",
        ],

        "Price": [
            "price",
            "cost",
            "pricing",
            "value for money",
            "value",
            "expensive",
            "cheap",
            "affordable",
        ],

        "Service": [
            "service",
            "support",
            "customer service",
            "customer support",
        ],

        "Staff": [
            "staff",
            "employee",
            "agent",
            "representative",
        ],

        "Delivery": [
            "delivery",
            "shipping",
            "shipment",
            "courier",
        ],

        "Packaging": [
            "packaging",
            "package",
            "box",
        ],

        "Performance": [
            "performance",
            "speed",
            "slow",
            "lag",
            "lagging",
        ],

        "Design": [
            "design",
            "appearance",
            "look",
            "style",
        ],

        "Ease of Use": [
            "easy to use",
            "ease of use",
            "user friendly",
            "user-friendly",
            "difficult to use",
        ],

        "Features": [
            "feature",
            "features",
            "function",
            "functionality",
        ],

        "Reliability": [
            "reliability",
            "reliable",
            "unreliable",
        ],

        "Experience": [
            "experience",
            "overall experience",
            "overall",
        ],
    },
}
# ---------------------------------------------------------------------------
# Complaint / severity signal terms — used by the priority engine
# ---------------------------------------------------------------------------
COMPLAINT_TERMS = {
    # term: severity weight (0-1)
    "refund": 0.6, "money deducted": 0.9, "never received": 0.95,
    "not received": 0.85, "wrong product": 0.75, "wrong item": 0.75,
    "defective": 0.7, "broken": 0.65, "damaged": 0.65, "scam": 1.0,
    "fraud": 1.0, "no response": 0.7, "not responded": 0.7,
    "unresolved": 0.6, "still waiting": 0.5, "cancelled my order": 0.6,
    "charged twice": 0.85, "missing item": 0.6, "late": 0.35,
    "delayed": 0.35, "poor packaging": 0.3, "slightly": 0.1,
    "worst experience": 0.85, "never buying again": 0.7,
    "waste of money": 0.6, "does not work": 0.7, "stopped working": 0.7,
    "safety": 0.8, "unsafe": 0.8, "injury": 0.9, "leaking": 0.55,
}

REPEAT_INDICATORS = ["again", "still", "every time", "repeatedly", "keeps happening", "second time", "third time"]
