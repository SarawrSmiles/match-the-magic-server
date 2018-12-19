from flask import Flask
from flask import request
from flask_cors import CORS
from flask_mysqldb import MySQL
from flask import jsonify
import datetime
import json

app = Flask(__name__)
CORS(app)

#Configuration
app.config['MYSQL_HOST'] = 'rds-mysql-sarah.ched3otliuj2.us-west-1.rds.amazonaws.com'
app.config['MYSQL_USER'] = 'SarahStrawn'
app.config['MYSQL_PASSWORD'] = 'big5carr0t'
app.config['MYSQL_DB'] = 'DisneyboundRef'


mysql = MySQL(app)

@app.route('/')
def hi():
    return str("hi")

@app.route('/colors')
def fetch_colors():
    cur = mysql.connection.cursor()
    cur.execute('''SELECT Colors.name, Colors.hex, Characters.name, CharacterColors.hex, Colors.complement, Garments.type, Garments.svg
                   FROM CharacterColors, Colors, Characters, Garments 
                   WHERE CharacterColors.color_id = Colors.id 
                   AND Garments.id = CharacterColors.garment_id
                   AND CharacterColors.character_id = Characters.id 
                   ORDER BY Colors.id''')
    results = cur.fetchall()
    
    colors = []
    for result in results:
        color_name       = str(result[0])
        color_hex        = str(result[1])
        character_name   = str(result[2])
        character_hex    = str(result[3])
        color_complement = str(result[4])
        garment_type     = str(result[5])
        garment_svg      = str(result[6])

        seen = False

        for color in colors:
            if color["name"] == color_name:
                color["characters"].append({"name": character_name, "hex": character_hex, "garment": garment_type, "svg": garment_svg})
                seen = True
                break
        if not seen:
            colors.append({
                    "name" : color_name,  
                    "hex" : color_hex,
                    "complement": color_complement,
                    "characters" : [{"name": character_name, "hex": character_hex, "garment": garment_type}]
                })

    cur.close()
    return json.dumps(colors)

    
@app.route('/colorshelper')
def colors_helper():
    cur = mysql.connection.cursor()
    cur.execute('''SELECT CharacterColors.id, Characters.name, Colors.name, CharacterColors.hex, CharacterColors.article, CharacterColors.importance, CharacterColors.outfit_name
                   FROM CharacterColors, Characters, Colors
                   WHERE CharacterColors.color_id = Colors.id
                   AND CharacterColors.character_id = Characters.id
                   AND CharacterColors.article IS NULL''')
    results = cur.fetchall()
    
    color_map = []
    html_object = "<ul>"
    for result in results:
        color_id = str(result[0])
        character_name = str(result[1])
        color_name = str(result[2])
        color_hex= str(result[3])
        article = str(result[4])
        importance = str(result[5])
        outfit_name = str(result[6])

        html_object = html_object + "<li style='padding: 10px;'>" + color_id + ": " + character_name + " ("+ outfit_name + ") <span class='color' style='background-color: " + color_hex + "; margin: 0 5px; padding: 3px;'>" + color_name + "</span> <span style='min-width: 20px; border-bottom: 1px solid black; margin: 0 5px;'> " + article + "</span> <span class='importance'> " + importance + "</span></li>"

    html_object = html_object + "</ul>"


    return html_object


@app.route('/movies')
def fetch_movies():
    cur = mysql.connection.cursor()
    cur.execute('''SELECT Movies.title FROM Movies WHERE sarah_green_light = 1 ORDER BY year''')
    results = cur.fetchall()
    movies = []
    for result in results:
        movies.append(result[0])

    cur.close()
    return json.dumps(movies)

@app.route('/assignBestFriends', methods=['GET', 'POST'])
def assignBestFriendship():
    if request.method == 'POST':
        friend1 = str(request.form['friend1'])
        friend2 = str(request.form['friend2'])
        print friend1, friend2

        cur = mysql.connection.cursor()
        cur.execute('''INSERT INTO BestFriends (friend_id_1, friend_id_2) VALUES (
        (SELECT id FROM Characters WHERE name = %s),
        (SELECT id FROM Characters WHERE name = %s)
        )''', [friend1, friend2])
        mysql.connection.commit()

        cur.close()
    return "bffs"

@app.route('/assignMovieToCharacter', methods=['GET', 'POST'])
def assignMovieToCharacter():
    if request.method == 'POST':
        print "prepping to assign a movie"
        movie_title = str(request.form['movie_title'])
        character_name = str(request.form['character_name'])

        cur = mysql.connection.cursor()
        cur.execute('''SELECT id FROM Characters WHERE name=%s''', [character_name])
        results = cur.fetchall()

        if len(results) == 0:
            cur.execute('''INSERT INTO Characters (name) VALUES (%s)''', [character_name])
            mysql.connection.commit()
            cur.execute('''SELECT id FROM Characters WHERE name=%s''', [character_name])
            results = cur.fetchall()

        character_id = results[0][0]
 
        cur.execute('''SELECT id FROM Movies WHERE title=%s''', [movie_title])
        results = cur.fetchall()
        movie_id = results[0][0]

        print "Movie id:", movie_id, "Character id:", character_id

        cur.execute('''INSERT INTO MovieCharacters (movie_id, character_id) VALUES (%s, %s)''', [movie_id, character_id])
        mysql.connection.commit()
        
        print "assigned"
        cur.close()
    return "hi"

@app.route('/addCharacterByColor', methods=['GET', 'POST'])
def addCharacterByColor():
    if request.method == 'POST':
        color = str(request.form['color'])
        character = str(request.form['character'])
        character_hex = str(request.form['hex'])
        character_outfit = str(request.form['outfit'])

        print "Making", character, color
        cur = mysql.connection.cursor()
        cur.execute('''SELECT id FROM Characters WHERE name=%s''', [character])
        results = cur.fetchall()

        if len(results) == 0:
            cur.execute('''INSERT INTO Characters (name) VALUES (%s)''', [character])
            mysql.connection.commit()
            cur.execute('''SELECT id FROM Characters WHERE name=%s''', [character])
            results = cur.fetchall()

        character_id = results[0][0]
        print character_id

        cur.execute('''SELECT id FROM Colors WHERE name=%s''', [color])
        results = cur.fetchall()
        color_id = results[0][0]

        cur.execute('''INSERT INTO CharacterColors (character_id, color_id, hex, outfit_name) VALUES (%s, %s, %s, %s)''', [character_id, color_id, character_hex, character_outfit])
        mysql.connection.commit()

        cur.close()
    return "hi"

@app.route('/movie/<title>')
def fetch_movie(title):
    movie_info = {
        "title" : title
    }

    cur = mysql.connection.cursor()
    cur.execute('''SELECT Characters.name
                   FROM MovieCharacters, Characters, Movies
                   WHERE MovieCharacters.character_id = Characters.id
                   AND MovieCharacters.movie_id = Movies.id
                   AND Movies.title =%s''' ,[title]) 

    results = cur.fetchall()
    characters = []
    for result in results:
        characters.append({
            "name": result[0],
        })  

    movie_info["characters"] = characters

    cur.close()
    print [movie_info]
    return json.dumps([movie_info])

@app.route('/outfits/<name>')
def fetch_character_outfits(name):
    cur = mysql.connection.cursor()
    cur.execute('''SELECT CharacterColors.outfit_name
                    FROM CharacterColors, Characters
                    WHERE CharacterColors.character_id = Characters.id
                    AND Characters.name =%s
                    GROUP BY CharacterColors.outfit_name''', [name])
    results = cur.fetchall()
    return json.dumps(results)

@app.route('/characters/<name>')
def fetch_character(name):
    cur = mysql.connection.cursor()
    cur.execute('''SELECT id FROM Characters WHERE name=%s''', [name])
    results = cur.fetchall()

    character_id = results[0][0]
    cur.execute('''SELECT Colors.name, CharacterColors.hex, CharacterColors.importance, CharacterColors.article, CharacterColors.outfit_name 
                   FROM CharacterColors, Colors, Characters 
                   WHERE CharacterColors.color_id = Colors.id 
                   AND CharacterColors.character_id = Characters.id 
                   AND Characters.name=%s ''', [name])

    results = cur.fetchall()

    character_attributes = { "name" : name}

    colors = []
        
    for result in results:
        colors.append({
            "name": result[0],
            "hex": result[1],
        })  

    outfits = []
    for result in results:
        new_outfit = {}
        color_name = str(result[0])
        color_hex = str(result[1])
        outfit_name = str(result[4])
        importance = result[2],
        article = result[3]

        seen = False
        for outfit in outfits:
            if outfit["name"] == outfit_name:
                outfit["colors"].append({ "name" : color_name,
                                          "hex"  : color_hex,
                                          "importance": importance,
                                          "article": article })
                outfit["stripped"] = outfit_name.lower().replace(" ", "")
                seen = True
                break
        if not seen:
            new_outfit["name"] = outfit_name
            new_outfit["colors"] = [{ "name" : color_name,
                                       "hex"  : color_hex,
                                      "importance": importance,
                                      "article": article  }]
            new_outfit["stripped"] = outfit_name.lower().replace(" ", "")
            outfits.append(new_outfit)

    character_attributes["outfits"] = outfits

    cur.execute('''SELECT Movies.title
                   FROM MovieCharacters, Movies
                   WHERE MovieCharacters.movie_id = Movies.id
                   AND MovieCharacters.character_id =%s ORDER BY Movies.year''' ,[character_id]) 

    results = cur.fetchall()
    movies = []
    for result in results:
        movies.append({
            "title": result[0],
        })  

    character_attributes["movies"] = movies


    related_characters=[]
    for movie in movies:
        cur.execute('''SELECT Characters.name
        FROM Characters, MovieCharacters, Movies
        WHERE Characters.id = MovieCharacters.character_id
        AND MovieCharacters.movie_id = Movies.id
        AND Movies.title = %s''', [movie["title"]])

        results = cur.fetchall()

        for result in results:
            for item in result:
                if (item not in related_characters) and (item != name):
                    related_characters.append(item)

    character_attributes["related_characters"] = related_characters

    cur.execute('''SELECT Characters.name
                   FROM BestFriends, Characters
                   WHERE (BestFriends.friend_id_1 = Characters.id
                   AND BestFriends.friend_id_2 = %s)
                   OR (BestFriends.friend_id_2 = Characters.id 
                   AND BestFriends.friend_id_1 = %s)
                   ''', [character_id, character_id])
                   
    results = cur.fetchall()
    if (len(results) > 0):
        character_attributes["best_friend"] = results[0]


    cur.execute('''SELECT MAX(id) FROM Characters''')
    max_character_id = int(cur.fetchall()[0][0])
    cur.execute('''SELECT Characters.name, Characters.id FROM Characters''')
    results = cur.fetchall()
    next_character_id = int(character_id + 1)
    all_characters = []
    for result in results:
        all_characters.append({"name": str(result[0]),
                             "id" : int(result[1])});


    next_character_id = character_id + 1
    next_character = []
    while (len(next_character) == 0) :
        next_character = [character for character in all_characters if character['id'] == next_character_id] 
        print next_character_id, max_character_id
        if next_character_id >= max_character_id:
            next_character_id = 1
        else:
            next_character_id = next_character_id + 1


    character_attributes["next"] = next_character[0]["name"]
 
    cur.close()
  
    return json.dumps([character_attributes]) 

if __name__ == '__main__':
    app.run(debug=True)
