"""Seed the album catalog with well-known albums across genres.

Searches MusicBrainz by artist+title, fetches metadata + genres, and persists to DB.
Skips albums that already exist locally.

Usage (inside Docker container):
    python -m backend.seed_catalog
"""

import asyncio
import logging

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from backend.app.core.database import async_session_maker
from backend.app.models.album import Album, Artist
from backend.app.services.musicbrainz import musicbrainz_client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# (artist, album title) pairs — diverse genres, decades, popularity levels.
SEED_ALBUMS = [
    # --- Hip-Hop / Rap ---
    ("Kendrick Lamar", "good kid, m.A.A.d city"),
    ("Kendrick Lamar", "To Pimp a Butterfly"),
    ("Kanye West", "My Beautiful Dark Twisted Fantasy"),
    ("Kanye West", "The College Dropout"),
    ("Nas", "Illmatic"),
    ("Jay-Z", "The Blueprint"),
    ("OutKast", "Aquemini"),
    ("A Tribe Called Quest", "The Low End Theory"),
    ("Travis Scott", "ASTROWORLD"),
    ("Tyler, the Creator", "IGOR"),
    ("J. Cole", "2014 Forest Hills Drive"),
    ("MF DOOM", "Mm.. Food"),
    ("Wu-Tang Clan", "Enter the Wu-Tang (36 Chambers)"),
    ("Eminem", "The Marshall Mathers LP"),

    # --- R&B / Soul ---
    ("Frank Ocean", "Blonde"),
    ("Frank Ocean", "channel ORANGE"),
    ("SZA", "Ctrl"),
    ("The Weeknd", "After Hours"),
    ("D'Angelo", "Voodoo"),
    ("Stevie Wonder", "Songs in the Key of Life"),
    ("Marvin Gaye", "What's Going On"),
    ("Lauryn Hill", "The Miseducation of Lauryn Hill"),

    # --- Rock / Alternative ---
    ("Radiohead", "In Rainbows"),
    ("Nirvana", "In Utero"),
    ("The Strokes", "Is This It"),
    ("Arctic Monkeys", "Whatever People Say I Am, That's What I'm Not"),
    ("Arcade Fire", "Funeral"),
    ("My Bloody Valentine", "Loveless"),
    ("Pixies", "Doolittle"),
    ("Weezer", "Weezer"),

    # --- Pop ---
    ("Beyoncé", "Lemonade"),
    ("Michael Jackson", "Thriller"),
    ("Prince", "Sign o' the Times"),
    ("Kate Bush", "Hounds of Love"),
    ("Charli XCX", "Brat"),
    ("Billie Eilish", "When We All Fall Asleep, Where Do We Go?"),
    ("Lorde", "Melodrama"),

    # --- Electronic / Dance ---
    ("Daft Punk", "Discovery"),
    ("Daft Punk", "Random Access Memories"),
    ("Aphex Twin", "Selected Ambient Works 85-92"),
    ("Boards of Canada", "Music Has the Right to Children"),
    ("Jamie xx", "In Colour"),

    # --- Jazz ---
    ("Miles Davis", "Kind of Blue"),
    ("John Coltrane", "A Love Supreme"),
    ("Charles Mingus", "The Black Saint and the Sinner Lady"),

    # --- Country / Folk / Singer-Songwriter ---
    ("Johnny Cash", "At Folsom Prison"),
    ("Bob Dylan", "Highway 61 Revisited"),
    ("Joni Mitchell", "Blue"),
    ("Nick Drake", "Pink Moon"),
    ("Elliott Smith", "Either/Or"),

    # --- Punk / Post-Punk ---
    ("Joy Division", "Unknown Pleasures"),
    ("Talking Heads", "Remain in Light"),
    ("The Clash", "London Calling"),

    # --- Metal ---
    ("Black Sabbath", "Paranoid"),
    ("Metallica", "Master of Puppets"),

    # --- Indie / Dream Pop ---
    ("Tame Impala", "Currents"),
    ("Beach House", "Depression Cherry"),
    ("Bon Iver", "For Emma, Forever Ago"),
    ("Sufjan Stevens", "Illinois"),

    # --- Latin / World ---
    ("Bad Bunny", "Un Verano Sin Ti"),
    ("Rosalía", "El Mal Querer"),

    # --- Ambient / Experimental ---
    ("Brian Eno", "Ambient 1: Music for Airports"),
    ("Björk", "Homogenic"),

    # =============================================
    # TOP ALBUMS 2015-2025
    # =============================================

    # --- 2015 ---
    ("Kendrick Lamar", "good kid, m.A.A.d city"),
    ("Adele", "25"),
    ("Grimes", "Art Angels"),
    ("Carly Rae Jepsen", "Emotion"),
    ("Father John Misty", "I Love You, Honeybear"),
    ("Courtney Barnett", "Sometimes I Sit and Think, and Sometimes I Just Sit"),
    ("Vince Staples", "Summertime '06"),
    ("Tame Impala", "Currents"),
    ("Alabama Shakes", "Sound & Color"),
    ("Sufjan Stevens", "Carrie & Lowell"),

    # --- 2016 ---
    ("Beyoncé", "Lemonade"),
    ("David Bowie", "Blackstar"),
    ("Solange", "A Seat at the Table"),
    ("A Tribe Called Quest", "We Got It from Here... Thank You 4 Your Service"),
    ("Anderson .Paak", "Malibu"),
    ("Chance the Rapper", "Coloring Book"),
    ("Kanye West", "The Life of Pablo"),
    ("Bon Iver", "22, A Million"),
    ("Rihanna", "Anti"),
    ("Noname", "Telefone"),

    # --- 2017 ---
    ("Kendrick Lamar", "DAMN."),
    ("Tyler, the Creator", "Flower Boy"),
    ("Sampha", "Process"),
    ("Brockhampton", "SATURATION III"),
    ("Vince Staples", "Big Fish Theory"),
    ("Fleet Foxes", "Crack-Up"),
    ("Mac DeMarco", "This Old Dog"),
    ("King Krule", "The OOZ"),
    ("Japanese Breakfast", "Soft Sounds from Another Planet"),
    ("Alvvays", "Antisocialites"),

    # --- 2018 ---
    ("Pusha T", "Daytona"),
    ("Kids See Ghosts", "Kids See Ghosts"),
    ("Earl Sweatshirt", "Some Rap Songs"),
    ("Mitski", "Be the Cowboy"),
    ("Kacey Musgraves", "Golden Hour"),
    ("Mac Miller", "Swimming"),
    ("Janelle Monáe", "Dirty Computer"),
    ("Blood Orange", "Negro Swan"),
    ("Noname", "Room 25"),
    ("Idles", "Joy as an Act of Resistance"),

    # --- 2019 ---
    ("Tyler, the Creator", "IGOR"),
    ("Billie Eilish", "When We All Fall Asleep, Where Do We Go?"),
    ("Little Simz", "GREY Area"),
    ("Solange", "When I Get Home"),
    ("FKA twigs", "Magdalene"),
    ("Freddie Gibbs", "Bandana"),
    ("Denzel Curry", "ZUU"),
    ("Weyes Blood", "Titanic Rising"),
    ("Vampire Weekend", "Father of the Bride"),
    ("Clairo", "Immunity"),

    # --- 2020 ---
    ("Fiona Apple", "Fetch the Bolt Cutters"),
    ("Run the Jewels", "RTJ4"),
    ("Mac Miller", "Circles"),
    ("Phoebe Bridgers", "Punisher"),
    ("Dua Lipa", "Future Nostalgia"),
    ("Freddie Gibbs", "Alfredo"),
    ("Moses Sumney", "grae"),
    ("The Strokes", "The New Abnormal"),
    ("Jessie Ware", "What's Your Pleasure?"),
    ("Yves Tumor", "Heaven to a Tortured Mind"),

    # --- 2021 ---
    ("Tyler, the Creator", "Call Me If You Get Lost"),
    ("Silk Sonic", "An Evening with Silk Sonic"),
    ("Little Simz", "Sometimes I Might Be Introvert"),
    ("Olivia Rodrigo", "SOUR"),
    ("Japanese Breakfast", "Jubilee"),
    ("Injury Reserve", "By the Time I Get to Phoenix"),
    ("Jazmine Sullivan", "Heaux Tales"),
    ("Turnstile", "Glow On"),
    ("Baby Keem", "The Melodic Blue"),
    ("St. Vincent", "Daddy's Home"),

    # --- 2022 ---
    ("Beyoncé", "Renaissance"),
    ("Kendrick Lamar", "Mr. Morale & The Big Steppers"),
    ("Steve Lacy", "Gemini Rights"),
    ("Alvvays", "Blue Rev"),
    ("Denzel Curry", "Melt My Eyez See Your Future"),
    ("Rosalía", "Motomami"),
    ("The Weeknd", "Dawn FM"),
    ("Big Thief", "Dragon New Warm Mountain I Believe in You"),
    ("JID", "The Forever Story"),
    ("Pusha T", "It's Almost Dry"),

    # --- 2023 ---
    ("Boygenius", "the record"),
    ("Olivia Rodrigo", "GUTS"),
    ("Travis Scott", "Utopia"),
    ("Caroline Polachek", "Desire, I Want to Turn Into You"),
    ("Sufjan Stevens", "Javelin"),
    ("Danny Brown", "Quaranta"),
    ("Jessie Ware", "That! Feels Good!"),
    ("Mitski", "The Land Is Inhospitable and So Are We"),
    ("Lana Del Rey", "Did You Know That There's a Tunnel Under Ocean Blvd"),
    ("100 gecs", "10,000 gecs"),

    # --- 2024 ---
    ("Charli XCX", "Brat"),
    ("Kendrick Lamar", "GNX"),
    ("Beyoncé", "Cowboy Carter"),
    ("MJ Lenderman", "Manning Fireworks"),
    ("Waxahatchee", "Tigers Blood"),
    ("Tyler, the Creator", "Chromakopia"),
    ("Adrianne Lenker", "Bright Future"),
    ("Billie Eilish", "Hit Me Hard and Soft"),
    ("Vampire Weekend", "Only God Was Above Us"),
    ("Kim Deal", "Nobody Loves You More"),

    # --- 2025 ---
    ("Kendrick Lamar", "GNX"),
    ("Doechii", "Alligator Bites Never Heal"),
    ("Clairo", "Charm"),
    ("Mac DeMarco", "One Wayne G"),

    # =============================================
    # CLASSIC / ESSENTIAL ADDITIONS
    # =============================================
    ("The Velvet Underground", "The Velvet Underground & Nico"),
    ("Fleetwood Mac", "Rumours"),
    ("The Smiths", "The Queen Is Dead"),
    ("The Cure", "Disintegration"),
    ("Portishead", "Dummy"),
    ("Massive Attack", "Mezzanine"),
    ("Erykah Badu", "Baduizm"),
    ("Outkast", "Stankonia"),
    ("Madvillain", "Madvillainy"),
    ("De La Soul", "3 Feet High and Rising"),
    ("The Notorious B.I.G.", "Ready to Die"),
    ("Lauryn Hill", "The Miseducation of Lauryn Hill"),
    ("Amy Winehouse", "Back to Black"),
    ("Gorillaz", "Demon Days"),
    ("LCD Soundsystem", "Sound of Silver"),
    ("Animal Collective", "Merriweather Post Pavilion"),
    ("Neutral Milk Hotel", "In the Aeroplane Over the Sea"),
    ("Wilco", "Yankee Hotel Foxtrot"),
    ("PJ Harvey", "Stories from the City, Stories from the Sea"),
    ("Jeff Buckley", "Grace"),
]


async def seed() -> None:
    async with async_session_maker() as db:
        # Load existing album titles for quick skip
        result = await db.execute(select(Album.title))
        existing_titles = {row[0].lower() for row in result.all()}

        created = 0
        skipped = 0
        failed = 0

        for i, (artist_name, album_title) in enumerate(SEED_ALBUMS):
            tag = f"[{i+1}/{len(SEED_ALBUMS)}]"

            if album_title.lower() in existing_titles:
                logger.info(f"  {tag} {album_title} — already exists, skipping")
                skipped += 1
                continue

            try:
                # Search MusicBrainz for this album
                query = f"{album_title} AND artist:{artist_name}"
                search_results = await musicbrainz_client.search_albums(query, limit=3)

                if not search_results:
                    logger.warning(f"  {tag} {artist_name} - {album_title}: no search results")
                    failed += 1
                    continue

                # Pick the best match (first result)
                best = search_results[0]

                # Verify it's not already in DB by mbid
                existing = await db.execute(
                    select(Album).where(Album.mbid == best.mbid)
                )
                if existing.scalar_one_or_none():
                    logger.info(f"  {tag} {album_title} — mbid already exists, skipping")
                    skipped += 1
                    existing_titles.add(album_title.lower())
                    continue

                # Fetch full details (with genres) by mbid
                mb = await musicbrainz_client.get_album_by_mbid(best.mbid)
                if not mb:
                    logger.warning(f"  {tag} {artist_name} - {album_title}: mbid detail fetch failed")
                    failed += 1
                    continue

                # Get or create artist
                artist = None
                if mb.artist_mbid:
                    artist_result = await db.execute(
                        select(Artist).where(Artist.mbid == mb.artist_mbid)
                    )
                    artist = artist_result.scalar_one_or_none()
                    if not artist:
                        artist = Artist(name=mb.artist_name, mbid=mb.artist_mbid)
                        db.add(artist)
                        await db.flush()

                album = Album(
                    mbid=mb.mbid,
                    title=mb.title,
                    release_year=mb.release_year,
                    cover_url=mb.cover_url,
                    genres=",".join(mb.genres) if mb.genres else None,
                )
                if artist:
                    album.artists.append(artist)
                db.add(album)
                await db.flush()

                existing_titles.add(album_title.lower())
                created += 1
                genres_str = ",".join(mb.genres or []) or "none"
                logger.info(
                    f"  {tag} {mb.title} by {mb.artist_name} "
                    f"({mb.release_year}) — genres: {genres_str}"
                )

            except Exception as e:
                logger.warning(f"  {tag} {artist_name} - {album_title}: error: {e}")
                failed += 1

        await db.commit()
        logger.info(
            f"Seed complete: {created} created, {skipped} skipped, {failed} failed "
            f"(total in DB now: {len(existing_titles)})"
        )


if __name__ == "__main__":
    asyncio.run(seed())
