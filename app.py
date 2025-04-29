import pickle
import streamlit as st
import requests
from concurrent.futures import ThreadPoolExecutor

# Constants
API_KEY = "8265bd1679663a7ea12ac168da84d2e8"
BASE_URL = "https://api.themoviedb.org/3/movie/{}?api_key={}&language=en-US"
TRENDING_URL = "https://api.themoviedb.org/3/trending/movie/week?api_key={}"
TOP_RATED_URL = "https://api.themoviedb.org/3/movie/top_rated?api_key={}&language=en-US&page=1"

# Set wide layout
st.set_page_config(layout="wide")

# Custom CSS for background image and styling
page_bg_img = '''
<style>
body {
background-image: url("https://images.unsplash.com/photo-1504384308090-c894fdcc538d");
background-size: cover;
background-repeat: no-repeat;
background-attachment: fixed;
}

.stApp {
background-color: rgba(0,0,0,0.6);
color: white;
padding: 20px;
border-radius: 10px;
}
</style>
'''
st.markdown(page_bg_img, unsafe_allow_html=True)

# Header
st.title('🎬 Movie Recommender System')

# Load data
movies = pickle.load(open('movie_list.pkl', 'rb'))
similarity = pickle.load(open('similarity.pkl', 'rb'))

# In-memory cache for movie details
movie_cache = {}

def fetch_movie_details(movie_id):
    if movie_id in movie_cache:
        return movie_cache[movie_id]
    
    try:
        response = requests.get(BASE_URL.format(movie_id, API_KEY))
        response.raise_for_status()
        data = response.json()
        poster_path = data.get('poster_path', '')
        overview = data.get('overview', 'No description available.')
        rating = data.get('vote_average', 'N/A')
        full_poster_url = f"https://image.tmdb.org/t/p/w500{poster_path}" if poster_path else ""
        
        # Cache the result
        movie_cache[movie_id] = (full_poster_url, overview, rating)
        return full_poster_url, overview, rating
    except Exception as e:
        return "", "Description unavailable.", "N/A"

def fetch_trending_movies():
    response = requests.get(TRENDING_URL.format(API_KEY))
    response.raise_for_status()
    data = response.json()['results']
    
    names, posters, overviews, ratings = [], [], [], []
    for movie in data:
        movie_id = movie['id']
        poster, overview, rating = fetch_movie_details(movie_id)
        names.append(movie['title'])
        posters.append(poster)
        overviews.append(overview)
        ratings.append(rating)
    
    return names, posters, overviews, ratings

def fetch_top_rated_movies():
    response = requests.get(TOP_RATED_URL.format(API_KEY))
    response.raise_for_status()
    data = response.json()['results']
    
    names, posters, overviews, ratings = [], [], [], []
    for movie in data:
        movie_id = movie['id']
        poster, overview, rating = fetch_movie_details(movie_id)
        names.append(movie['title'])
        posters.append(poster)
        overviews.append(overview)
        ratings.append(rating)
    
    return names, posters, overviews, ratings

def recommend(movie):
    if movie not in movies['title'].values:
        return [], [], [], []

    index = movies[movies['title'] == movie].index[0]
    distances = sorted(list(enumerate(similarity[index])), key=lambda x: x[1], reverse=True)[1:6]

    names, posters, overviews, ratings = [], [], [], []
    movie_ids = [movies.iloc[i[0]].movie_id for i in distances]

    # Fetch movie details in parallel
    with ThreadPoolExecutor(max_workers=5) as executor:
        results = executor.map(fetch_movie_details, movie_ids)

    # Process results
    for idx, result in enumerate(results):
        poster, overview, rating = result
        names.append(movies.iloc[distances[idx][0]].title)
        posters.append(poster)
        overviews.append(overview)
        ratings.append(rating)

    return names, posters, overviews, ratings

# Movie selection
movie_list = movies['title'].values
selected_movie = st.selectbox("🎥 Type or select a movie", movie_list)

# Option to choose between recommendations, trending, or top-rated movies
option = st.selectbox(
    "Choose the movie list to display",
    ["Recommended Movies", "Trending Movies", "Top-Rated Movies"]
)

# Show recommendations or trending/top-rated movies
if option == 'Recommended Movies':
    if st.button('🍿 Show Recommendations'):
        with st.spinner("Fetching recommendations..."):
            names, posters, overviews, ratings = recommend(selected_movie)
            if names:
                cols = st.columns(5)
                for idx, col in enumerate(cols):
                    with col:
                        st.image(posters[idx], use_container_width=True)
                        st.markdown(f"**{names[idx]}**")
                        st.caption(f"⭐ {ratings[idx]}/10")
                        st.write(overviews[idx][:150] + "...")
            else:
                st.warning("No recommendations found or movie not recognized.")
elif option == 'Trending Movies':
    if st.button('🍿 Show Trending Movies'):
        with st.spinner("Fetching trending movies..."):
            names, posters, overviews, ratings = fetch_trending_movies()
            if names:
                cols = st.columns(5)
                for idx, col in enumerate(cols):
                    with col:
                        st.image(posters[idx], use_container_width=True)
                        st.markdown(f"**{names[idx]}**")
                        st.caption(f"⭐ {ratings[idx]}/10")
                        st.write(overviews[idx][:150] + "...")
            else:
                st.warning("No trending movies found.")
elif option == 'Top-Rated Movies':
    if st.button('🍿 Show Top-Rated Movies'):
        with st.spinner("Fetching top-rated movies..."):
            names, posters, overviews, ratings = fetch_top_rated_movies()
            if names:
                cols = st.columns(5)
                for idx, col in enumerate(cols):
                    with col:
                        st.image(posters[idx], use_container_width=True)
                        st.markdown(f"**{names[idx]}**")
                        st.caption(f"⭐ {ratings[idx]}/10")
                        st.write(overviews[idx][:150] + "...")
            else:
                st.warning("No top-rated movies found.")
