from flask import Flask, render_template, request, redirect, session, abort
import sqlite3
import re
from pathlib import Path

BASE = Path(__file__).resolve().parent
DB = BASE / "cybernet97.db"

app = Flask(__name__)
app.secret_key = "cybernet97-1997-secret-key"


# =========================================================
# DATABASE
# =========================================================

def database():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():

    c = database()

    c.executescript("""

    CREATE TABLE IF NOT EXISTS counters(
        username TEXT PRIMARY KEY,
        views INTEGER DEFAULT 0
    );

    CREATE TABLE IF NOT EXISTS buttons(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        title TEXT,
        url TEXT,
        created TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS links(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        title TEXT,
        url TEXT,
        description TEXT,
        created TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS homepage_stats(
        username TEXT PRIMARY KEY,
        updated TEXT,
        email TEXT,
        midi TEXT
    );

    CREATE TABLE IF NOT EXISTS homepages(
        username TEXT PRIMARY KEY,
        title TEXT,
        bg TEXT,
        text_color TEXT,
        favorites TEXT
    );

    CREATE TABLE IF NOT EXISTS messenger_users(
        username TEXT PRIMARY KEY,
        password TEXT,
        status TEXT DEFAULT 'offline',
        away TEXT DEFAULT ''
    );

    CREATE TABLE IF NOT EXISTS buddies(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        buddy TEXT
    );

    CREATE TABLE IF NOT EXISTS messages(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sender TEXT,
        receiver TEXT,
        message TEXT,
        sent TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    """)

    # Some default CyberMessenger users.
    defaults = [
        (
            "CyberKid",
            "cyber",
            "online",
            "Working on my homepage!"
        ),
        (
            "PrincessPixel",
            "pixel",
            "away",
            "BRB making graphics!"
        ),
        (
            "DoomLord",
            "doom",
            "online",
            "Playing Doom II"
        ),
        (
            "Hackerman",
            "hack",
            "offline",
            ""
        ),
        (
            "XFilesFan",
            "xfiles",
            "online",
            "The truth is out there..."
        )
    ]

    for user in defaults:

        c.execute(
            """
            INSERT OR IGNORE INTO messenger_users
            (username,password,status,away)
            VALUES(?,?,?,?)
            """,
            user
        )

    # Default buddy lists.

    default_buddies = [
        ("CyberKid", "PrincessPixel"),
        ("CyberKid", "DoomLord"),
        ("CyberKid", "Hackerman"),
        ("CyberKid", "XFilesFan"),

        ("PrincessPixel", "CyberKid"),
        ("PrincessPixel", "DoomLord"),

        ("DoomLord", "CyberKid"),
        ("DoomLord", "Hackerman"),

        ("Hackerman", "CyberKid"),

        ("XFilesFan", "CyberKid")
    ]

    for username, buddy in default_buddies:

        c.execute(
            """
            INSERT OR IGNORE INTO buddies
            (username,buddy)
            VALUES(?,?)
            """,
            (username, buddy)
        )

    c.commit()
    c.close()


# =========================================================
# GLOBAL TEMPLATE VARIABLES
# =========================================================

@app.context_processor
def globals():

    return {
        "messenger_user": session.get("messenger_user")
    }


# =========================================================
# MAIN PAGE
# =========================================================

@app.route("/")
def index():

    return render_template("index.html")


# =========================================================
# HOMEPAGE BUILDER
# =========================================================

@app.route("/builder", methods=["GET", "POST"])
def builder():

    created = None

    if request.method == "POST":

        username = re.sub(
            r"[^a-zA-Z0-9_]",
            "",
            request.form.get("username", "")
        ).lower()

        title = request.form.get(
            "title",
            "My Totally Awesome Homepage"
        )

        bg = request.form.get(
            "bg",
            "#000080"
        )

        text_color = request.form.get(
            "text_color",
            "#ffffff"
        )

        favorites = request.form.get(
            "favorites",
            ""
        )

        if username:

            c = database()

            c.execute(
                """
                INSERT OR REPLACE INTO homepages
                (username,title,bg,text_color,favorites)
                VALUES(?,?,?,?,?)
                """,
                (
                    username,
                    title,
                    bg,
                    text_color,
                    favorites
                )
            )

            c.execute(
                """
                INSERT OR IGNORE INTO counters
                (username,views)
                VALUES(?,0)
                """,
                (username,)
            )

            c.execute(
                """
                INSERT OR REPLACE INTO homepage_stats
                (username,updated,email,midi)
                VALUES(?,?,?,?)
                """,
                (
                    username,
                    "September 13, 1997",
                    username + "@cybernet97.com",
                    "cyberdreams.mid"
                )
            )

            c.commit()
            c.close()

            created = username

    return render_template(
        "builder.html",
        created=created
    )


# =========================================================
# PERSONAL HOMEPAGES
# =========================================================

@app.route("/~<username>/")
def homepage(username):

    c = database()

    page = c.execute(
        """
        SELECT *
        FROM homepages
        WHERE username=?
        """,
        (username,)
    ).fetchone()

    if not page:
        c.close()
        abort(404)

    c.execute(
        """
        UPDATE counters
        SET views=views+1
        WHERE username=?
        """,
        (username,)
    )

    count = c.execute(
        """
        SELECT views
        FROM counters
        WHERE username=?
        """,
        (username,)
    ).fetchone()

    c.commit()
    c.close()

    return render_template(
        "custom_homepage.html",
        page=page,
        views=count["views"]
    )


# =========================================================
# HIT COUNTER
# =========================================================

@app.route("/counter/<username>")
def counter(username):

    c = database()

    user = c.execute(
        """
        SELECT views
        FROM counters
        WHERE username=?
        """,
        (username,)
    ).fetchone()

    c.close()

    if not user:
        return "NO COUNTER FOUND"

    return render_template(
        "counter.html",
        username=username,
        views=user["views"]
    )


# =========================================================
# BUTTON EXCHANGE
# =========================================================

@app.route("/buttons")
def buttons():

    c = database()

    buttons = c.execute(
        """
        SELECT *
        FROM buttons
        ORDER BY id DESC
        """
    ).fetchall()

    c.close()

    return render_template(
        "buttons.html",
        buttons=buttons
    )


@app.route("/buttons/add", methods=["POST"])
def add_button():

    username = request.form.get(
        "username",
        "Anonymous"
    )

    title = request.form.get(
        "title",
        "My Button"
    )

    url = request.form.get(
        "url",
        "#"
    )

    c = database()

    c.execute(
        """
        INSERT INTO buttons
        (username,title,url)
        VALUES(?,?,?)
        """,
        (
            username,
            title,
            url
        )
    )

    c.commit()
    c.close()

    return redirect("/buttons")


# =========================================================
# COOL LINKS
# =========================================================

@app.route("/links/<username>")
def links(username):

    c = database()

    links = c.execute(
        """
        SELECT *
        FROM links
        WHERE username=?
        ORDER BY id DESC
        """,
        (username,)
    ).fetchall()

    c.close()

    return render_template(
        "links.html",
        username=username,
        links=links
    )


@app.route("/links/add", methods=["POST"])
def add_link():

    username = request.form.get(
        "username",
        "anonymous"
    )

    title = request.form.get(
        "title",
        "Cool Website"
    )

    url = request.form.get(
        "url",
        "#"
    )

    description = request.form.get(
        "description",
        ""
    )

    c = database()

    c.execute(
        """
        INSERT INTO links
        (username,title,url,description)
        VALUES(?,?,?,?)
        """,
        (
            username,
            title,
            url,
            description
        )
    )

    c.commit()
    c.close()

    return redirect(
        "/links/" + username
    )


# =========================================================
# HOMEPAGE STATISTICS
# =========================================================

@app.route("/stats/<username>")
def stats(username):

    c = database()

    counter = c.execute(
        """
        SELECT *
        FROM counters
        WHERE username=?
        """,
        (username,)
    ).fetchone()

    info = c.execute(
        """
        SELECT *
        FROM homepage_stats
        WHERE username=?
        """,
        (username,)
    ).fetchone()

    c.close()

    return render_template(
        "stats.html",
        username=username,
        counter=counter,
        info=info
    )


# =========================================================
# CYBERMESSENGER
# =========================================================

@app.route("/messenger", methods=["GET", "POST"])
def messenger():

    error = None

    if request.method == "POST":

        username = request.form.get(
            "username",
            ""
        ).strip()

        password = request.form.get(
            "password",
            ""
        )

        c = database()

        user = c.execute(
            """
            SELECT *
            FROM messenger_users
            WHERE username=? AND password=?
            """,
            (
                username,
                password
            )
        ).fetchone()

        c.close()

        if user:

            session["messenger_user"] = user["username"]

            c = database()

            c.execute(
                """
                UPDATE messenger_users
                SET status='online'
                WHERE username=?
                """,
                (user["username"],)
            )

            c.commit()
            c.close()

            return redirect("/messenger")

        error = "Invalid screen name or password."

    if session.get("messenger_user"):

        return messenger_home()

    return render_template(
        "messenger.html",
        error=error
    )


def messenger_home():

    username = session.get(
        "messenger_user"
    )

    c = database()

    user = c.execute(
        """
        SELECT *
        FROM messenger_users
        WHERE username=?
        """,
        (username,)
    ).fetchone()

    buddies = c.execute(
        """
        SELECT
            b.buddy,
            u.status,
            u.away
        FROM buddies b
        LEFT JOIN messenger_users u
        ON b.buddy=u.username
        WHERE b.username=?
        ORDER BY b.buddy
        """,
        (username,)
    ).fetchall()

    c.close()

    return render_template(
        "messenger_home.html",
        user=user,
        buddies=buddies
    )


@app.route("/messenger/register", methods=["POST"])
def messenger_register():

    username = request.form.get(
        "username",
        ""
    ).strip()

    password = request.form.get(
        "password",
        ""
    )

    if not username or not password:
        return redirect("/messenger")

    username = re.sub(
        r"[^a-zA-Z0-9_]",
        "",
        username
    )

    c = database()

    try:

        c.execute(
            """
            INSERT INTO messenger_users
            (username,password,status,away)
            VALUES(?,?,?,?)
            """,
            (
                username,
                password,
                "online",
                ""
            )
        )

        c.commit()

    except sqlite3.IntegrityError:

        c.close()

        return render_template(
            "messenger.html",
            error="That screen name is already taken!"
        )

    c.close()

    session["messenger_user"] = username

    return redirect("/messenger")


@app.route("/messenger/logout")
def messenger_logout():

    username = session.get(
        "messenger_user"
    )

    if username:

        c = database()

        c.execute(
            """
            UPDATE messenger_users
            SET status='offline'
            WHERE username=?
            """,
            (username,)
        )

        c.commit()
        c.close()

    session.pop(
        "messenger_user",
        None
    )

    return redirect("/messenger")


@app.route(
    "/messenger/status",
    methods=["POST"]
)
def messenger_status():

    username = session.get(
        "messenger_user"
    )

    if not username:
        return redirect("/messenger")

    status = request.form.get(
        "status",
        "online"
    )

    away = request.form.get(
        "away",
        ""
    )

    if status not in [
        "online",
        "away",
        "offline"
    ]:
        status = "online"

    c = database()

    c.execute(
        """
        UPDATE messenger_users
        SET status=?, away=?
        WHERE username=?
        """,
        (
            status,
            away,
            username
        )
    )

    c.commit()
    c.close()

    return redirect("/messenger")


@app.route(
    "/messenger/add-buddy",
    methods=["POST"]
)
def messenger_add_buddy():

    username = session.get(
        "messenger_user"
    )

    if not username:
        return redirect("/messenger")

    buddy = request.form.get(
        "buddy",
        ""
    ).strip()

    c = database()

    exists = c.execute(
        """
        SELECT username
        FROM messenger_users
        WHERE username=?
        """,
        (buddy,)
    ).fetchone()

    if exists and buddy != username:

        c.execute(
            """
            INSERT INTO buddies
            (username,buddy)
            VALUES(?,?)
            """,
            (
                username,
                buddy
            )
        )

        c.commit()

    c.close()

    return redirect("/messenger")


@app.route(
    "/messenger/chat/<buddy>",
    methods=["GET", "POST"]
)
def messenger_chat(buddy):

    username = session.get(
        "messenger_user"
    )

    if not username:
        return redirect("/messenger")

    c = database()

    buddy_user = c.execute(
        """
        SELECT *
        FROM messenger_users
        WHERE username=?
        """,
        (buddy,)
    ).fetchone()

    if not buddy_user:
        c.close()
        abort(404)

    if request.method == "POST":

        message = request.form.get(
            "message",
            ""
        ).strip()

        if message:

            c.execute(
                """
                INSERT INTO messages
                (sender,receiver,message)
                VALUES(?,?,?)
                """,
                (
                    username,
                    buddy,
                    message
                )
            )

            c.commit()

    messages = c.execute(
        """
        SELECT *
        FROM messages
        WHERE
        (sender=? AND receiver=?)
        OR
        (sender=? AND receiver=?)
        ORDER BY id ASC
        """,
        (
            username,
            buddy,
            buddy,
            username
        )
    ).fetchall()

    c.close()

    return render_template(
        "messenger_chat.html",
        username=username,
        buddy=buddy_user,
        messages=messages
    )


# =========================================================
# EXISTING CYBERNET PAGES
# =========================================================

@app.route("/guestbook")
@app.route("/guestbook.html")
def guestbook():

    c = database()

    entries = []

    # Works with an existing guestbook table if your
    # previous version created one.
    try:

        entries = c.execute(
            """
            SELECT *
            FROM guestbook
            ORDER BY id DESC
            """
        ).fetchall()

    except sqlite3.OperationalError:
        pass

    c.close()

    return render_template(
        "guestbook.html",
        entries=entries
    )


@app.route(
    "/guestbook/sign",
    methods=["POST"]
)
def sign_guestbook():

    name = request.form.get(
        "name",
        "Anonymous"
    )

    message = request.form.get(
        "message",
        ""
    )

    c = database()

    try:

        c.execute(
            """
            INSERT INTO guestbook
            (name,message)
            VALUES(?,?)
            """,
            (
                name,
                message
            )
        )

        c.commit()

    except sqlite3.OperationalError:

        c.execute(
            """
            CREATE TABLE IF NOT EXISTS guestbook(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                message TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        c.execute(
            """
            INSERT INTO guestbook
            (name,message)
            VALUES(?,?)
            """,
            (
                name,
                message
            )
        )

        c.commit()

    c.close()

    return redirect("/guestbook")


# =========================================================
# SIMPLE PAGE ROUTES
# =========================================================

@app.route("/webring")
@app.route("/webring.html")
def webring():
    return render_template("webring.html")


@app.route("/email")
@app.route("/email.html")
def email():
    return render_template("email.html")


@app.route("/downloads")
@app.route("/downloads.html")
def downloads():
    return render_template("downloads.html")


@app.route("/underconstruction")
@app.route("/underconstruction.html")
def underconstruction():
    return render_template("underconstruction.html")


@app.route("/news")
@app.route("/news.html")
def news():
    return render_template("news.html")


@app.route("/music")
@app.route("/music.html")
def music():
    return render_template("music.html")


@app.route("/search")
@app.route("/search.html")
def search():
    return render_template("search.html")


@app.route("/directory")
@app.route("/directory.html")
def directory():
    return render_template("directory.html")


@app.route("/irc", methods=["GET", "POST"])
def irc():

    c = database()


    c.execute("""
        CREATE TABLE IF NOT EXISTS irc_channels(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE,
            description TEXT
        )
    """)


    c.execute("""
        CREATE TABLE IF NOT EXISTS irc_messages(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            channel TEXT,
            username TEXT,
            message TEXT,
            created TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)


    channels = [
        (
            "#general",
            "General CyberNet discussion"
        ),
        (
            "#gaming",
            "Video games and cheats"
        ),
        (
            "#music",
            "MIDI and MP3 discussion"
        ),
        (
            "#hackers",
            "Computers and programming"
        ),
        (
            "#xfiles",
            "Aliens and mysteries"
        )
    ]


    for channel in channels:

        c.execute(
            """
            INSERT OR IGNORE INTO irc_channels
            (name,description)
            VALUES(?,?)
            """,
            channel
        )



    selected = request.args.get(
        "channel",
        "#general"
    )



    if request.method == "POST":

        username = request.form.get(
            "username",
            "Guest"
        )


        message = request.form.get(
            "message",
            ""
        )


        if message:

            c.execute(
                """
                INSERT INTO irc_messages
                (channel,username,message)
                VALUES(?,?,?)
                """,
                (
                    selected,
                    username,
                    message
                )
            )



    messages = c.execute(
        """
        SELECT username,message,created
        FROM irc_messages
        WHERE channel=?
        ORDER BY id ASC
        """,
        (selected,)
    ).fetchall()



    c.commit()
    c.close()



    return render_template(
        "irc.html",
        channels=channels,
        selected=selected,
        messages=messages
    )


@app.route("/bbs", methods=["GET","POST"])
def bbs():

    c = database()


    c.execute("""
        CREATE TABLE IF NOT EXISTS bbs_posts(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            message TEXT,
            created TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)


    if request.method == "POST":

        username = request.form.get(
            "username",
            "Anonymous"
        )

        message = request.form.get(
            "message",
            ""
        )


        if message:

            c.execute(
                """
                INSERT INTO bbs_posts
                (username,message)
                VALUES(?,?)
                """,
                (
                    username,
                    message
                )
            )


    posts = c.execute(
        """
        SELECT *
        FROM bbs_posts
        ORDER BY id DESC
        """
    ).fetchall()


    c.commit()
    c.close()


    return render_template(
        "bbs.html",
        posts=posts
    )


@app.route("/classified")
def classified():
    return render_template("classified.html")


@app.route("/mall")
def mall():

    c = database()


    c.execute("""
        CREATE TABLE IF NOT EXISTS products(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            description TEXT,
            price REAL
        )
    """)


    products = [

        (
            "CyberNet T-Shirt",
            "Official CyberNet 97 shirt",
            19.99
        ),

        (
            "Netscape Navigator CD",
            "Latest browser upgrade",
            9.99
        ),

        (
            "Cool Animated GIF Pack",
            "500 awesome GIFs",
            4.99
        ),

        (
            "MIDI Music Collection",
            "100 internet songs",
            7.99
        ),

        (
            "Java Applet Collection",
            "Interactive web programs",
            12.99
        )

    ]



    for product in products:

        c.execute(
            """
            INSERT OR IGNORE INTO products
            (name,description,price)
            VALUES(?,?,?)
            """,
            product
        )



    items = c.execute(
        """
        SELECT *
        FROM products
        """
    ).fetchall()



    c.commit()
    c.close()



    return render_template(
        "mall.html",
        products=items,
        total=0
    )



@app.route("/mall/buy", methods=["POST"])
def mall_buy():

    return redirect("/mall")
@app.route("/awards")
def awards():
    return render_template("awards.html")


@app.route("/browserwars", methods=["GET", "POST"])
def browserwars():

    c = database()

    c.execute("""
        CREATE TABLE IF NOT EXISTS browser_votes(
            browser TEXT PRIMARY KEY,
            votes INTEGER DEFAULT 0
        )
    """)

    browsers = [
        "netscape",
        "internet_explorer"
    ]

    for browser in browsers:
        c.execute(
            """
            INSERT OR IGNORE INTO browser_votes
            (browser, votes)
            VALUES (?, 0)
            """,
            (browser,)
        )

    if request.method == "POST":

        choice = request.form.get("browser")

        if choice in browsers:
            c.execute(
                """
                UPDATE browser_votes
                SET votes = votes + 1
                WHERE browser = ?
                """,
                (choice,)
            )

    results = c.execute(
        """
        SELECT browser, votes
        FROM browser_votes
        """
    ).fetchall()

    votes = {
        row["browser"]: row["votes"]
        for row in results
    }

    total = sum(votes.values())

    c.commit()
    c.close()

    return render_template(
        "browserwars.html",
        votes=votes,
        total=total
    )


@app.route("/gifs")
def gifs():
    return render_template("gifs.html")


@app.route("/ufo")
def ufo():
    return render_template("ufo_incident.html")


@app.route("/java")
def java():
    return render_template("java.html")


@app.route("/portal")
def portal():
    return render_template("portal.html")


@app.route("/worldmap")
def worldmap():
    return render_template("worldmap.html")


@app.route("/source")
def source():
    return render_template("source.html")


@app.route("/secret/terminal")
def secret_terminal():
    return render_template("secret_terminal.html")


# =========================================================
# PERSONAL HOMEPAGE ALIASES
# =========================================================

@app.route("/~cyberkid/")
def cyberkid():
    return render_template(
        "sites/cyberkid.html"
    )


@app.route("/~princesspixel/")
def princesspixel():
    return render_template(
        "sites/princesspixel.html"
    )


@app.route("/~doomlord/")
def doomlord():
    return render_template(
        "sites/doomlord.html"
    )


@app.route("/~xfilesfan/")
def xfilesfan():
    return render_template(
        "sites/xfilesfan.html"
    )


@app.route("/~hackerman/")
def hackerman():
    return render_template(
        "sites/hackerman.html"
    )
    
@app.route("/strange")
def strange():

    return render_template(
        "strange.html"
    )


@app.route("/strange/area51")
def area51():

    return render_template(
        "area51.html"
    )


@app.route("/strange/haunted")
def haunted():

    return render_template(
        "haunted.html"
    )


@app.route("/strange/chain")
def chain():

    return render_template(
        "chain.html"
    )


@app.route("/strange/hacker")
def hacker():

    return render_template(
        "hacker.html"
    )


# =========================================================
# START
# =========================================================

if __name__ == "__main__":

    init_db()

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=False,
        use_reloader=False
    )