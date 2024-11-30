from flask import Flask, render_template, request, jsonify, session , redirect ,url_for
import psycopg2
import sorting
from scraping import scrape_list
import json
import time
import io
import csv
import secrets
app = Flask(__name__)


#Secret Key
secret_key = secrets.token_hex(32)
app.secret_key = secret_key

@app.before_request
def before_any_request():
    if 'changelog' not in session:
            session['changelog'] = ""  # Initialize 'changelog' if not already defined
    if 'loadedLog' not in session:
        session['loadedLog'] = False # false by default
    if request.method == 'GET':
        if request.path == '/list':
            session['changelog'] = ""
            

@app.route('/graphs')
def graphs():
    listID = request.args.get('id')
    listData=  getIndividualListData(listID)
    return render_template("graphs.html",listData=listData)

@app.route('/')
def index():

    x = getListsData()
    return render_template('lists.html',lists=x)

@app.route('/scraping', methods=['POST'])
def scrape():
    #print("asdfoiupqwieotujeqwklas;chfioauf;lkj")
    listurl = request.json['listurl']
    #listurl = request.json['url']
    movies = scrape_list(listurl)
    #print("upppppppppppppppppppppppppppppppppppppppppppppppppp")
    print(movies)
    insert_list(movies)
    return "{}"

def insert_list(movies):
    #print("Inserting List")
    #print(movies)
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        #print(movies["title"])
        #print(movies["url"])
        
        #print("Insert Movielist")
        # Insert list into the database and retrieve the generated movieListId
        cursor.execute("""
            INSERT INTO movielist (title, url)
            VALUES (%s, %s)
            ON CONFLICT (url)  
            DO UPDATE 
            SET title = EXCLUDED.title
            RETURNING "movielistID";
        """, (movies["title"], movies["url"]))

        #print("Insert Movie_Movielist")
        movie_list_id = cursor.fetchone()[0]
        cursor.execute("""
            DELETE FROM movie_movielist
            WHERE "movielistID" = %s;
        """, (movie_list_id,))

        print("Insert movies")
        # Insert movies into the movie table and retrieve the generated movieId

        
        for movie in movies["movies"]:
            #print("mov")
            cursor.execute("""
                INSERT INTO movie (title, watches,releaseyear,runtime)
                VALUES (%s, %s,%s,%s)
                ON CONFLICT (title,releaseyear)
                DO UPDATE 
                SET watches = EXCLUDED.watches
                RETURNING "movieID";
            """, (movie["title"], movie["watches"],movie["releaseyear"],movie["runtime"],))
            #print("finmov")
            # Fetch the generated movieId
            movie_id = cursor.fetchone()[0]
            
            # Insert into the movie_movieList join table
            cursor.execute("""
                INSERT INTO movie_movielist ("movieID", "movielistID")
                VALUES (%s, %s)
                ON CONFLICT ("movieID", "movielistID") DO NOTHING;
            """, (movie_id, movie_list_id))
            #Insert Genres
            for genre in movie["genres"]:
                # Insert the genre, ignoring conflict if it already exists
                cursor.execute("""
                    INSERT INTO genre (name)
                    VALUES (%s)
                    ON CONFLICT (name) DO NOTHING
                    RETURNING "genreID";
                """, (genre,))
                
                # Fetch the genreID (fetchone might return None if there was a conflict)
                genre_id = cursor.fetchone()
                if genre_id is None:
                    # If there was a conflict, fetch the existing genreID
                    cursor.execute("""
                        SELECT "genreID" FROM genre WHERE name = %s;
                    """, (genre,))
                    genre_id = cursor.fetchone()[0]
                else:
                    genre_id = genre_id[0]

                # Insert the relationship into the movie_genre join table
                cursor.execute("""
                    INSERT INTO movie_genre ("movieID", "genreID")
                    VALUES (%s, %s)
                    ON CONFLICT ("movieID", "genreID") DO NOTHING;
                """, (movie_id, genre_id))
            



        conn.commit()


        
        
    except Exception as e:
        conn.rollback()
        #print(f"An error occurred: {e}")
    finally:
        cursor.close()
        conn.close()



@app.route('/list')
def test():
    listID = request.args.get('id')
    list = getIndividualListData(listID)
    
    return render_template('list view.html',list=list)

@app.route('/sort', methods=['POST'])
def sort():
    listID = request.args.get('id')
    list = getIndividualListData(listID)
    sorting.sortfilms(list['movies'])
    #print("Fin sort")
    #print(list["movies"])
    return list['movies']


#Route for generating changelog
@app.route('/generatelog',methods=['POST'])
def generatelog():
    #print("Generating Log")
    data = request.get_json()  # Get the JSON data from the request body

    original_list = data.get('originalList')
    print(original_list)
    sorted_list = data.get('currentList')
    #print(sorted_list)
    differences = calculate_differences(original_list,sorted_list)
    changelogString = generate_changelog(original_list,differences)
    #print(differences)
    #print("Changelog")

    session["changelog"] = changelogString
    session["loadedLog"] = True
    #print(changelogString)

    return '{}'
    

#Route for sending changelog across
@app.route('/changelog')
def changelog():
    print("Changelog route")
    changelog = session.get('changelog', '')
    
    
   
        
    return render_template("changelog.html", log=changelog)

    

    
def getListsData():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""SELECT * FROM movielist""")

    lists = cursor.fetchall()

    lists_as_dictionaries = []

    for list in lists:
        listDictionary = {}
        listDictionary["movielistID"] = list[0]
        listDictionary["title"] = list[1]
        listDictionary["url"] = list[2]
        lists_as_dictionaries.append(listDictionary)
    
    return lists_as_dictionaries

def getIndividualListData(listID):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""SELECT * FROM movielist WHERE movielist."movielistID" = %s;""", (listID,))
    
    lists = cursor.fetchone()

    listDictionary = {}

    listDictionary['movielistID']=lists[0]
    listDictionary['title']=lists[1]
    listDictionary['url']=lists[2]

    cursor.execute("""SELECT * FROM movie JOIN movie_movielist ON movie."movieID"=movie_movielist."movieID" JOIN movielist ON movielist."movielistID"=movie_movielist."movielistID" WHERE movielist."movielistID" = %s;""", (listID,))
    
    movies_as_dictionaries = []
    movies = cursor.fetchall()
    for movie in movies:
        movieDictionary = {}
        movieDictionary["movieID"] = movie[0]
        movieDictionary["title"] = movie[1]
        movieDictionary["watches"] = movie[2]
        movieDictionary["releaseyear"] = movie[3]
        movieDictionary["runtime"] = movie[4]
        #Get genres
        cursor.execute("""SELECT name
                        FROM genre 
                        JOIN movie_genre mg ON genre."genreID" = mg."genreID"
                        WHERE mg."movieID" = %s;
                       """,(movieDictionary["movieID"],))
        genres = cursor.fetchall()
        genres = [genre[0] for genre in genres]
        movieDictionary["genres"] = genres
        movies_as_dictionaries.append(movieDictionary)
    listDictionary['movies'] = movies_as_dictionaries
    #print(listDictionary)
    return listDictionary

#Start Up a connection to the database
def get_db_connection():
    conn = psycopg2.connect(
        host='localhost',
        database='moviesultimate',
        user='postgres',
        password='pass'
    )
    return conn


#original_list = [{'movieID': '3', 'title': 'Elio', 'watches': '175'}, {'movieID': '4', 'title': 'John Wick Presents: Ballerina', 'watches': '350'}]
#sorted_list = [{'movieID': '4', 'title': 'John Wick Presents: Ballerina', 'watches': '350'}, {'movieID': '3', 'title': 'Elio', 'watches': '175'}]

def calculate_differences(original_list, sorted_list):
    #print("yahoo")
    #print(original_list)
    original_indices = {movie["movieID"]: i for i, movie in enumerate(original_list)}
    #print("original indices")
    #print(original_indices)
    differences = []
    for new_index, movie in enumerate(sorted_list):
        movieID = movie["movieID"]
        #print(movieID)
        if movieID in original_indices:
            original_index = original_indices[movieID]
            difference = new_index - original_index
            differences.append(difference)
        else:
            differences.append(None)
    return differences

def generate_changelog(original_list, differences):
    result = ""
    result += "Gained places:\n"
    for i in range(0, len(original_list)):
        if(differences[i]>0):
            print("DIFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF")
            result += original_list[i]["title"] + " +" + str(differences[i]) + " \n"

    result += "Lost places:\n"
    for i in range(0, len(original_list)):
        if(differences[i]<0):
            result += original_list[i]["title"] + " " + str(differences[i]) + " \n"
    #print(result)
    return result



#differences = calculate_differences(original_list, sorted_list)
#print(differences)
#generate_changelog(original_list, differences)


if __name__ == '__main__':
    app.run(debug=True)