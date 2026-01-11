#!/usr/bin/env python3
"""
YouTube Video Upload Script
Uploads a video from a URL (e.g., Cloudinary) to YouTube using YouTube Data API v3
"""

import os
import sys
import json
import argparse
import requests
from pathlib import Path
from typing import Optional

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError


class YouTubeUploader:
    """Handles YouTube video uploads using the YouTube Data API v3"""

    SCOPES = ['https://www.googleapis.com/auth/youtube.upload']
    API_SERVICE_NAME = 'youtube'
    API_VERSION = 'v3'

    def __init__(self, client_id: str, client_secret: str, refresh_token: str):
        """
        Initialize YouTube uploader with OAuth credentials

        Args:
            client_id: Google OAuth client ID
            client_secret: Google OAuth client secret
            refresh_token: Google OAuth refresh token
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.refresh_token = refresh_token
        self.youtube = None

    def authenticate(self):
        """Authenticate with YouTube API using refresh token"""
        try:
            credentials = Credentials.from_authorized_user_info(
                info={
                    'client_id': self.client_id,
                    'client_secret': self.client_secret,
                    'refresh_token': self.refresh_token,
                },
                scopes=self.SCOPES
            )

            self.youtube = build(
                self.API_SERVICE_NAME,
                self.API_VERSION,
                credentials=credentials
            )
            print("✓ Successfully authenticated with YouTube API")

        except Exception as e:
            print(f"✗ Authentication failed: {e}", file=sys.stderr)
            sys.exit(1)

    def download_video(self, video_url: str, output_path: str) -> bool:
        """
        Download video from URL

        Args:
            video_url: URL of the video to download
            output_path: Path to save the downloaded video

        Returns:
            True if download successful, False otherwise
        """
        try:
            print(f"Downloading video from: {video_url}")

            response = requests.get(video_url, stream=True, timeout=300)
            response.raise_for_status()

            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0

            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)

                        if total_size > 0:
                            progress = (downloaded / total_size) * 100
                            print(f"\rDownload progress: {progress:.1f}%", end='')

            print(f"\n✓ Video downloaded successfully: {output_path}")
            print(f"  File size: {downloaded / (1024*1024):.2f} MB")
            return True

        except requests.exceptions.RequestException as e:
            print(f"\n✗ Failed to download video: {e}", file=sys.stderr)
            return False
        except Exception as e:
            print(f"\n✗ Unexpected error during download: {e}", file=sys.stderr)
            return False

    def upload_video(
        self,
        video_file: str,
        title: str,
        description: str = '',
        tags: Optional[list] = None,
        category_id: str = '22',
        privacy_status: str = 'private'
    ) -> Optional[str]:
        """
        Upload video to YouTube

        Args:
            video_file: Path to video file to upload
            title: Video title
            description: Video description
            tags: List of tags
            category_id: YouTube category ID (default: 22 = People & Blogs)
            privacy_status: Privacy status (private, public, unlisted)

        Returns:
            Video ID if successful, None otherwise
        """
        if not self.youtube:
            print("✗ Not authenticated. Call authenticate() first.", file=sys.stderr)
            return None

        try:
            body = {
                'snippet': {
                    'title': title,
                    'description': description,
                    'tags': tags or [],
                    'categoryId': category_id
                },
                'status': {
                    'privacyStatus': privacy_status,
                    'selfDeclaredMadeForKids': False
                }
            }

            print(f"\nUploading video to YouTube...")
            print(f"  Title: {title}")
            print(f"  Privacy: {privacy_status}")

            media = MediaFileUpload(
                video_file,
                chunksize=1024*1024,
                resumable=True
            )

            request = self.youtube.videos().insert(
                part=','.join(body.keys()),
                body=body,
                media_body=media
            )

            response = None
            while response is None:
                status, response = request.next_chunk()
                if status:
                    progress = int(status.progress() * 100)
                    print(f"\rUpload progress: {progress}%", end='')

            video_id = response['id']
            video_url = f"https://www.youtube.com/watch?v={video_id}"

            print(f"\n✓ Upload successful!")
            print(f"  Video ID: {video_id}")
            print(f"  Video URL: {video_url}")

            return video_id

        except HttpError as e:
            print(f"\n✗ YouTube API error: {e}", file=sys.stderr)
            return None
        except Exception as e:
            print(f"\n✗ Upload failed: {e}", file=sys.stderr)
            return None


def main():
    parser = argparse.ArgumentParser(
        description='Upload video to YouTube from URL'
    )
    parser.add_argument(
        '--video-url',
        required=True,
        help='URL of the video to upload (e.g., Cloudinary URL)'
    )
    parser.add_argument(
        '--title',
        required=True,
        help='Video title'
    )
    parser.add_argument(
        '--description',
        default='',
        help='Video description'
    )
    parser.add_argument(
        '--tags',
        default='',
        help='Comma-separated list of tags'
    )
    parser.add_argument(
        '--category-id',
        default='22',
        help='YouTube category ID (default: 22 = People & Blogs)'
    )
    parser.add_argument(
        '--privacy',
        default='private',
        choices=['private', 'public', 'unlisted'],
        help='Privacy status (default: private)'
    )

    args = parser.parse_args()

    # Get credentials from environment variables
    client_id = os.environ.get('YOUTUBE_CLIENT_ID')
    client_secret = os.environ.get('YOUTUBE_CLIENT_SECRET')
    refresh_token = os.environ.get('YOUTUBE_REFRESH_TOKEN')

    if not all([client_id, client_secret, refresh_token]):
        print("✗ Missing required environment variables:", file=sys.stderr)
        print("  - YOUTUBE_CLIENT_ID", file=sys.stderr)
        print("  - YOUTUBE_CLIENT_SECRET", file=sys.stderr)
        print("  - YOUTUBE_REFRESH_TOKEN", file=sys.stderr)
        sys.exit(1)

    # Parse tags
    tags = [tag.strip() for tag in args.tags.split(',') if tag.strip()]

    # Initialize uploader
    uploader = YouTubeUploader(client_id, client_secret, refresh_token)
    uploader.authenticate()

    # Download video
    video_filename = 'temp_video.mp4'
    if not uploader.download_video(args.video_url, video_filename):
        sys.exit(1)

    try:
        # Upload to YouTube
        video_id = uploader.upload_video(
            video_file=video_filename,
            title=args.title,
            description=args.description,
            tags=tags,
            category_id=args.category_id,
            privacy_status=args.privacy
        )

        if video_id:
            # Output result as JSON for easy parsing
            result = {
                'success': True,
                'video_id': video_id,
                'video_url': f"https://www.youtube.com/watch?v={video_id}"
            }
            print(f"\n{json.dumps(result, indent=2)}")
            sys.exit(0)
        else:
            result = {
                'success': False,
                'error': 'Upload failed'
            }
            print(f"\n{json.dumps(result, indent=2)}", file=sys.stderr)
            sys.exit(1)

    finally:
        # Clean up downloaded file
        if os.path.exists(video_filename):
            os.remove(video_filename)
            print(f"✓ Cleaned up temporary file: {video_filename}")


if __name__ == '__main__':
    main()
