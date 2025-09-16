from fastapi import APIRouter, HTTPException, status
from app import models_pydantic as schemas
from app.services.supabase_storage import supabase_storage_service

router = APIRouter()


@router.post("/uploads/presign", response_model=schemas.SupabaseUploadResponse)
async def create_presigned_upload(upload_request: schemas.SupabaseUploadRequest):
    """Create a presigned upload URL for direct Supabase Storage upload."""

    # Validate content type
    allowed_types = [
        'audio/mpeg', 'audio/mp3', 'audio/wav', 'audio/m4a', 'audio/aac',
        'audio/ogg', 'audio/flac', 'audio/x-wav', 'audio/mp4'
    ]

    if upload_request.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Content type {upload_request.content_type} not allowed. "
                   f"Allowed types: {', '.join(allowed_types)}"
        )

    try:
        upload_data = supabase_storage_service.create_upload_url(
            project_id=upload_request.project_id,
            filename=upload_request.filename,
            content_type=upload_request.content_type,
            expires_in=3600  # 1 hour
        )

        return schemas.SupabaseUploadResponse(
            signed_url=upload_data['signed_url'],
            file_path=upload_data['file_path'],
            public_url=upload_data['public_url']
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate presigned upload: {str(e)}"
        )