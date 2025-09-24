from typing import List, Optional, Dict, Any
from uuid import UUID, uuid4
from datetime import datetime
import random

from supabase import Client
from app.models_pydantic import Artist, ArtistCreate


class ArtistService:
    """Service for managing artist data and reference images."""

    def __init__(self, supabase_client: Client):
        self.supabase = supabase_client

    async def create_artist(self, artist_data: ArtistCreate, user_id: str) -> Artist:
        """
        Create a new artist with reference images.

        Args:
            artist_data: Artist creation data including reference images
            user_id: ID of the user creating the artist

        Returns:
            Created Artist object

        Raises:
            Exception: If creation fails
        """
        try:
            # Insert artist into database
            result = self.supabase.table('artists').insert({
                'name': artist_data.name,
                'description': artist_data.description,
                'reference_image_urls': artist_data.reference_image_urls,
                'user_id': user_id,
                'created_at': datetime.now().isoformat()
            }).execute()

            if not result.data:
                raise Exception("Failed to create artist")

            artist_row = result.data[0]
            return Artist(
                id=UUID(artist_row['id']),
                name=artist_row['name'],
                description=artist_row['description'],
                reference_image_urls=artist_row['reference_image_urls'],
                created_at=datetime.fromisoformat(artist_row['created_at'])
            )

        except Exception as e:
            raise Exception(f"Failed to create artist: {e}")

    async def get_artist_by_id(self, artist_id: UUID) -> Optional[Artist]:
        """
        Retrieve an artist by ID.

        Args:
            artist_id: UUID of the artist

        Returns:
            Artist object if found, None otherwise
        """
        try:
            result = self.supabase.table('artists').select('*').eq('id', str(artist_id)).execute()

            if not result.data:
                return None

            artist_row = result.data[0]
            return Artist(
                id=UUID(artist_row['id']),
                name=artist_row['name'],
                description=artist_row['description'],
                reference_image_urls=artist_row['reference_image_urls'],
                created_at=datetime.fromisoformat(artist_row['created_at'])
            )

        except Exception as e:
            raise Exception(f"Failed to get artist: {e}")

    async def list_artists(self, limit: int = 100, offset: int = 0) -> List[Artist]:
        """
        List all artists with pagination.

        Args:
            limit: Maximum number of artists to return
            offset: Number of artists to skip

        Returns:
            List of Artist objects
        """
        try:
            result = (
                self.supabase.table('artists')
                .select('*')
                .order('created_at', desc=True)
                .range(offset, offset + limit - 1)
                .execute()
            )

            artists = []
            for row in result.data:
                artists.append(Artist(
                    id=UUID(row['id']),
                    name=row['name'],
                    description=row['description'],
                    reference_image_urls=row['reference_image_urls'],
                    created_at=datetime.fromisoformat(row['created_at'])
                ))

            return artists

        except Exception as e:
            raise Exception(f"Failed to list artists: {e}")

    async def update_artist(self, artist_id: UUID, update_data: Dict[str, Any]) -> Optional[Artist]:
        """
        Update an artist's information.

        Args:
            artist_id: UUID of the artist to update
            update_data: Dictionary of fields to update

        Returns:
            Updated Artist object if successful, None if not found
        """
        try:
            result = (
                self.supabase.table('artists')
                .update(update_data)
                .eq('id', str(artist_id))
                .execute()
            )

            if not result.data:
                return None

            artist_row = result.data[0]
            return Artist(
                id=UUID(artist_row['id']),
                name=artist_row['name'],
                description=artist_row['description'],
                reference_image_urls=artist_row['reference_image_urls'],
                created_at=datetime.fromisoformat(artist_row['created_at'])
            )

        except Exception as e:
            raise Exception(f"Failed to update artist: {e}")

    async def delete_artist(self, artist_id: UUID) -> bool:
        """
        Delete an artist.

        Args:
            artist_id: UUID of the artist to delete

        Returns:
            True if deletion successful, False if artist not found
        """
        try:
            result = (
                self.supabase.table('artists')
                .delete()
                .eq('id', str(artist_id))
                .execute()
            )

            return len(result.data) > 0

        except Exception as e:
            raise Exception(f"Failed to delete artist: {e}")

    def select_reference_image_for_project(
        self,
        artist_reference_urls: List[str],
        project_id: UUID
    ) -> str:
        """
        Select a consistent reference image for an artist within a project.
        Uses project_id as seed for reproducible random selection.

        Args:
            artist_reference_urls: List of reference image URLs for the artist
            project_id: UUID of the project (used as seed)

        Returns:
            Selected reference image URL
        """
        if not artist_reference_urls:
            raise ValueError("Artist must have at least one reference image")

        # Use project ID as seed for consistent selection within project
        random.seed(str(project_id))
        selected_url = random.choice(artist_reference_urls)

        # Reset random seed to avoid affecting other random operations
        random.seed()

        return selected_url

    async def get_artists_by_ids(self, artist_ids: List[UUID]) -> List[Artist]:
        """
        Get multiple artists by their IDs.

        Args:
            artist_ids: List of artist UUIDs

        Returns:
            List of Artist objects
        """
        if not artist_ids:
            return []

        try:
            str_ids = [str(artist_id) for artist_id in artist_ids]
            result = (
                self.supabase.table('artists')
                .select('*')
                .in_('id', str_ids)
                .execute()
            )

            artists = []
            for row in result.data:
                artists.append(Artist(
                    id=UUID(row['id']),
                    name=row['name'],
                    description=row['description'],
                    reference_image_urls=row['reference_image_urls'],
                    created_at=datetime.fromisoformat(row['created_at'])
                ))

            return artists

        except Exception as e:
            raise Exception(f"Failed to get artists by IDs: {e}")