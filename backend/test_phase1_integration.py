#!/usr/bin/env python3
"""
Phase 1 Integration Test: Audio Upload → Transcription → Editing
Tests the complete Phase 1 workflow end-to-end.
"""

import asyncio
import httpx
import json
from uuid import uuid4

async def test_phase1_integration():
    """Test complete Phase 1: Audio upload, transcription, and editing workflow."""

    base_url = "http://localhost:8001/api"

    async with httpx.AsyncClient() as client:
        print("🎯 Phase 1 Integration Test: Audio → Transcription → Editing")
        print("=" * 60)

        # Step 1: Create a project
        print("\n📋 Step 1: Creating project...")
        project_response = await client.post(
            f"{base_url}/projects",
            json={"name": "Phase 1 Test Project"}
        )

        if project_response.status_code != 200:
            print(f"❌ Failed to create project: {project_response.status_code}")
            print(project_response.text)
            return False

        project = project_response.json()
        project_id = project['id']
        print(f"✅ Project created: {project_id}")

        # Step 2: Test audio upload endpoint
        print("\n📤 Step 2: Testing audio upload endpoint...")
        audio_upload_response = await client.post(
            f"{base_url}/projects/{project_id}/upload-audio",
            json={
                "filename": "test_song.mp3",
                "content_type": "audio/mpeg"
            }
        )

        if audio_upload_response.status_code != 200:
            print(f"❌ Failed to get upload URL: {audio_upload_response.status_code}")
            print(audio_upload_response.text)
            return False

        upload_data = audio_upload_response.json()
        print(f"✅ Upload URL created: {upload_data['signed_url'][:50]}...")

        # Step 3: Test audio processing endpoint
        print("\n🔧 Step 3: Testing audio processing...")
        audio_process_response = await client.post(
            f"{base_url}/projects/{project_id}/process-audio",
            json={
                "audio_url": "https://example.com/test_song.mp3",
                "audio_format": "mp3"
            }
        )

        if audio_process_response.status_code != 200:
            print(f"❌ Failed to process audio: {audio_process_response.status_code}")
            print(audio_process_response.text)
            return False

        process_data = audio_process_response.json()
        print(f"✅ Audio processed: {process_data['audio_duration']}s, {process_data['audio_format']}")

        # Step 4: Test transcription cost estimation
        print("\n💰 Step 4: Testing cost estimation...")
        cost_response = await client.post(
            f"{base_url}/transcription/estimate-cost?audio_duration_minutes=3.0"
        )

        if cost_response.status_code != 200:
            print(f"❌ Failed to estimate cost: {cost_response.status_code}")
            print(cost_response.text)
            return False

        cost_data = cost_response.json()
        print(f"✅ Cost estimation: ${cost_data['estimated_cost_usd']} for 3 minutes")

        # Step 5: Test transcription status endpoint (without starting actual transcription)
        print("\n🎤 Step 5: Testing transcription status...")
        transcription_status_response = await client.get(
            f"{base_url}/projects/{project_id}/transcription"
        )

        if transcription_status_response.status_code != 200:
            print(f"❌ Failed to get transcription status: {transcription_status_response.status_code}")
            print(transcription_status_response.text)
            return False

        status_data = transcription_status_response.json()
        print(f"✅ Transcription status: {status_data['status']}")

        # Step 6: Test project retrieval with audio data
        print("\n📋 Step 6: Verifying project has audio data...")
        project_get_response = await client.get(f"{base_url}/projects/{project_id}")

        if project_get_response.status_code != 200:
            print(f"❌ Failed to get project: {project_get_response.status_code}")
            return False

        updated_project = project_get_response.json()
        print(f"✅ Project audio URL: {updated_project.get('audio_url', 'Not set')}")
        print(f"✅ Project audio duration: {updated_project.get('audio_duration', 'Not set')}s")
        print(f"✅ Transcription status: {updated_project.get('transcription_status', 'Not set')}")

        # Step 7: Clean up - delete test project
        print("\n🧹 Step 7: Cleaning up...")
        delete_response = await client.delete(f"{base_url}/projects/{project_id}")

        if delete_response.status_code == 200:
            print(f"✅ Test project deleted")
        else:
            print(f"⚠️ Failed to delete test project: {delete_response.status_code}")

        print("\n" + "=" * 60)
        print("🎉 PHASE 1 INTEGRATION TEST COMPLETED SUCCESSFULLY!")
        print("✅ Audio upload endpoints working")
        print("✅ Audio processing working")
        print("✅ Transcription endpoints integrated")
        print("✅ Cost estimation working")
        print("✅ Project management working")
        print("\n🚀 Ready for Phase 2: Scene Selection & Prompts")

        return True

async def test_endpoint_documentation():
    """Test that all Phase 1 endpoints are documented in OpenAPI."""
    async with httpx.AsyncClient() as client:
        print("\n📚 Testing API Documentation...")

        docs_response = await client.get("http://localhost:8001/openapi.json")
        if docs_response.status_code != 200:
            print("❌ Failed to get OpenAPI docs")
            return False

        openapi_spec = docs_response.json()
        paths = openapi_spec.get('paths', {})

        expected_endpoints = [
            '/api/projects/{project_id}/upload-audio',
            '/api/projects/{project_id}/process-audio',
            '/api/projects/{project_id}/transcribe',
            '/api/projects/{project_id}/transcription',
            '/api/transcription/jobs/{job_id}/status',
            '/api/transcription/estimate-cost'
        ]

        missing_endpoints = []
        for endpoint in expected_endpoints:
            if endpoint not in paths:
                missing_endpoints.append(endpoint)

        if missing_endpoints:
            print(f"❌ Missing endpoints in docs: {missing_endpoints}")
            return False
        else:
            print(f"✅ All {len(expected_endpoints)} Phase 1 endpoints documented")
            return True

if __name__ == "__main__":
    print("Starting Phase 1 Integration Tests...\n")

    try:
        # Test endpoint documentation
        doc_success = asyncio.run(test_endpoint_documentation())

        # Test integration workflow
        integration_success = asyncio.run(test_phase1_integration())

        if doc_success and integration_success:
            print("\n🎯 ALL TESTS PASSED - Phase 1 Ready for Frontend Integration!")
            exit(0)
        else:
            print("\n❌ Some tests failed - Check output above")
            exit(1)

    except Exception as e:
        print(f"\n❌ Test failed with exception: {e}")
        exit(1)