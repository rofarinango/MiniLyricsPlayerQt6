"""
Mini Player with Spotify Integration and Lyrics Display
This application allows users to:
1. Log in to Spotify - not implemented yet
2. View recently played songs
3. Display lyrics for the selected song
"""

from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QListWidget, QLabel, QScrollArea
from PyQt6.QtCore import Qt
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import requests
from typing import List, Dict
import sys
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class MiniPlayer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
            client_id=os.getenv('SPOTIFY_CLIENT_ID'),
            client_secret=os.getenv('SPOTIFY_CLIENT_SECRET'),
            redirect_uri='http://localhost:8888/callback',
            scope='user-read-recently-played',
        ))
        
        # Set up the main window
        self.setWindowTitle("Lyrics Mini Player")
        self.setGeometry(100, 100, 300, 250)
        # Create main widget and layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)

        # Create UI elements
        self.setup_ui()
        
        # Load recently played tracks
        self.load_recent_tracks()

    def setup_ui(self):
        """
        Set up the user interface elements:
        1. Create a list widget for recently played tracks
        2. Create a scrollable label for displaying lyrics
        3. Create buttons for login and refresh
        4. Add all elements to the layout
        """
        self.track_list = QListWidget()
        self.track_list.itemClicked.connect(self.on_track_selected)
        self.layout.addWidget(self.track_list)

        # Create a scroll area for lyrics
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.hide()  # Hide the scroll area initially
        
        # Create a container widget for the lyrics label
        self.lyrics_container = QWidget()
        self.lyrics_layout = QVBoxLayout(self.lyrics_container)
        
        self.lyrics_label = QLabel()
        self.lyrics_label.setWordWrap(True)
        self.lyrics_layout.addWidget(self.lyrics_label)
        
        # Set the container widget as the scroll area's widget
        self.scroll_area.setWidget(self.lyrics_container)
        self.layout.addWidget(self.scroll_area)

        self.login_button = QPushButton("Login with Spotify")
        #self.login_button.clicked.connect(self.login_with_spotify)
        self.layout.addWidget(self.login_button)

        self.refresh_button = QPushButton("Refresh Tracks")
        self.refresh_button.clicked.connect(self.refresh_tracks)    
        self.layout.addWidget(self.refresh_button)

        self.central_widget.setLayout(self.layout)

    def load_recent_tracks(self):
        """
        Load the 10 most recently played tracks:
        1. Call Spotify API to get recently played tracks
        2. Extract track information (name, artist, album)
        3. Add tracks to the list widget
        """
        try:
            results = self.sp.current_user_recently_played(limit=10)
            tracks = results['items']
            for track in tracks:
                track_name = track['track']['name']
                artist_name = track['track']['artists'][0]['name']
                self.track_list.addItem(f"{track_name} - {artist_name}")
        except Exception as e:
            print(f"Error loading recent tracks: {e}")

    def display_lyrics(self, track_name: str, artist_name: str):
        """
        Display lyrics for the selected track:
        1. Use a lyrics API (e.g., Genius, Musixmatch) to fetch lyrics
        2. Update the lyrics label with the fetched text
        3. Handle cases where lyrics are not available
        """
        try:
            lyrics = self.get_lyrics(track_name, artist_name)
            self.lyrics_label.setText(lyrics)
        except Exception as e:
            print(f"Error displaying lyrics: {e}")
            self.lyrics_label.setText("Error fetching lyrics")

    def on_track_selected(self):
        """
        Handle track selection:
        1. Get the selected track from the list widget
        2. Extract track and artist information
        3. Call display_lyrics with the track information
        """
        selected_item = self.track_list.currentItem()
        if selected_item:
            track_name, artist_name = selected_item.text().split(" - ")
            self.display_lyrics(track_name, artist_name)
            self.scroll_area.show()  # Show the scroll area when a track is selected
            print(f"Track selected: {track_name} - {artist_name}")
        else:
            self.scroll_area.hide()  # Hide the scroll area if no track is selected

    def refresh_tracks(self):
        """
        Refresh the list of recently played tracks:
        1. Clear the current list
        2. Call load_recent_tracks to update the list
        """
        self.track_list.clear()
        self.load_recent_tracks()

    def login_with_spotify(self):
        """
        Handle Spotify login:
        1. Open the Spotify authorization URL in a web browser
        2. Handle the redirect back to the application
        """
        pass

    def get_lyrics(self, track_name: str, artist_name: str) -> str:
        """
        Fetch lyrics for a given track using Genius API:
        1. Search for the song using track name and artist
        2. Return the fetched lyrics
        """
        try:
            import lyricsgenius
            # Initialize Genius API client with token from environment variables
            genius = lyricsgenius.Genius(os.getenv('GENIUS_ACCESS_TOKEN'))
            
            # Search for the song
            song = genius.search_song(track_name, artist_name)
            
            if song:
                return song.lyrics
            else:
                return "Lyrics not found"
                
        except Exception as e:
            print(f"Error fetching lyrics: {e}")
            return "Error fetching lyrics. Please try again later."

# Main application entry point
if __name__ == '__main__':
    # Create and run the application
    app = QApplication(sys.argv)
    player = MiniPlayer()
    player.show()
    sys.exit(app.exec())
    pass
