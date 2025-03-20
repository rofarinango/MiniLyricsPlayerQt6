"""
Mini Player with Spotify Integration and Lyrics Display
This application allows users to:
1. Log in to Spotify - not implemented yet
2. View recently played songs
3. Display lyrics for the selected song
"""

from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QBoxLayout, QVBoxLayout, QHBoxLayout, QPushButton, QListWidget, QLabel, QScrollArea
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QPixmap
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import requests
from typing import List, Dict
import sys
import os
from dotenv import load_dotenv
from io import BytesIO

# Load environment variables from .env file
load_dotenv()

class LyricsWorker(QThread):
    lyrics_ready = pyqtSignal(str)
    error_occurred = pyqtSignal(str)

    def __init__(self, track_name: str, artist_name: str):
        super().__init__()
        self.track_name = track_name
        self.artist_name = artist_name

    def run(self):
        try:
            import lyricsgenius
            genius = lyricsgenius.Genius(os.getenv('GENIUS_ACCESS_TOKEN'))
            song = genius.search_song(self.track_name, self.artist_name)
            
            if song:
                self.lyrics_ready.emit(song.lyrics)
            else:
                self.lyrics_ready.emit("Lyrics not found")
        except Exception as e:
            self.error_occurred.emit(str(e))

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
        self.setGeometry(100, 100, 300, 300)  # Reduced width and height
        # Create main widget and layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)
        self.layout.setSpacing(5)  # Reduced spacing between widgets
        self.layout.setContentsMargins(5, 5, 5, 5)  # Reduced margins

        # Store track data
        self.track_data = {}  # Dictionary to store track information
        self.lyrics_worker = None  # Store the current lyrics worker

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
        # Create a container for the image to center it
        image_container = QWidget()
        image_container_layout = QHBoxLayout(image_container)
        image_container_layout.setContentsMargins(0, 0, 0, 0)
        image_container_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Create image label
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setFixedSize(200, 200)  # Made image smaller
        self.image_label.setStyleSheet("""
            QLabel {
                background-color: #f0f0f0;
                border: 1px solid #ddd;
                border-radius: 5px;
            }
        """)
        image_container_layout.addWidget(self.image_label)
        self.layout.addWidget(image_container)

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

        #self.login_button = QPushButton("Login with Spotify")
        #self.login_button.clicked.connect(self.login_with_spotify)
        #self.layout.addWidget(self.login_button)

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
            self.track_data.clear()  # Clear previous track data
            
            for track in tracks:
                track_name = track['track']['name']
                artist_name = track['track']['artists'][0]['name']
                image_url = track['track']['album']['images'][0]['url']  # Get image URL directly
                
                # Store track data
                self.track_data[f"{track_name} - {artist_name}"] = {
                    'name': track_name,
                    'artist': artist_name,
                    'image_url': image_url
                }
                
                self.track_list.addItem(f"{track_name} - {artist_name}")
            
            # Load image for the first track
            if tracks:
                first_track = tracks[0]
                track_name = first_track['track']['name']
                artist_name = first_track['track']['artists'][0]['name']
                self.display_image(track_name, artist_name)
        except Exception as e:
            print(f"Error loading recent tracks: {e}")

    def display_image(self, track_name: str, artist_name: str):
        """
        Display the image for the selected track using stored image URL
        """
        try:
            track_key = f"{track_name} - {artist_name}"
            if track_key in self.track_data:
                image_url = self.track_data[track_key]['image_url']
                # Download the image
                response = requests.get(image_url)
                image_data = BytesIO(response.content)
                
                # Create QPixmap and scale it to fit the label
                pixmap = QPixmap()
                pixmap.loadFromData(image_data.getvalue())
                
                # Scale the pixmap to fit the label while maintaining aspect ratio
                scaled_pixmap = pixmap.scaled(
                    200,  # Reduced width
                    200,  # Reduced height
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
                
                self.image_label.setPixmap(scaled_pixmap)
            else:
                self.image_label.setText("No image available")
        except Exception as e:
            print(f"Error displaying image: {e}")
            self.image_label.setText("Error loading image")

    def display_lyrics(self, track_name: str, artist_name: str):
        """
        Display lyrics for the selected track:
        1. Use a lyrics API (e.g., Genius, Musixmatch) to fetch lyrics
        2. Update the lyrics label with the fetched text
        3. Handle cases where lyrics are not available
        """
        # Show loading message
        self.lyrics_label.setText("Loading lyrics...")
        self.scroll_area.show()

        # Cancel any existing lyrics worker
        if self.lyrics_worker and self.lyrics_worker.isRunning():
            self.lyrics_worker.terminate()
            self.lyrics_worker.wait()

        # Create and start new lyrics worker
        self.lyrics_worker = LyricsWorker(track_name, artist_name)
        self.lyrics_worker.lyrics_ready.connect(self.update_lyrics)
        self.lyrics_worker.error_occurred.connect(self.handle_lyrics_error)
        self.lyrics_worker.start()

    def update_lyrics(self, lyrics: str):
        """
        Update the lyrics label with the fetched lyrics
        """
        if lyrics == "Lyrics not found":
            self.lyrics_label.setText("No lyrics available for this track.")
        else:
            self.lyrics_label.setText(lyrics)

    def handle_lyrics_error(self, error: str):
        """
        Handle errors from the lyrics worker
        """
        print(f"Error fetching lyrics: {error}")
        self.lyrics_label.setText("Error fetching lyrics. Please try again later.")

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
            # Update image immediately
            self.display_image(track_name, artist_name)
            # Start loading lyrics in background
            self.display_lyrics(track_name, artist_name)
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

# Main application entry point
if __name__ == '__main__':
    # Create and run the application
    app = QApplication(sys.argv)
    player = MiniPlayer()
    player.show()
    sys.exit(app.exec())
    pass
