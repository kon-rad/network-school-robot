import asyncio
import base64
import json
import os
import cv2
import numpy as np
from datetime import datetime
from typing import Optional, List, Dict
from pathlib import Path
import google.generativeai as genai
from ..config import get_settings

settings = get_settings()

# Storage directory for known faces
FACES_DIR = Path(__file__).parent.parent.parent / "data" / "faces"
FACES_DIR.mkdir(parents=True, exist_ok=True)


class PersonRecognitionService:
    def __init__(self):
        self.api_key = settings.gemini_api_key
        self.enabled = bool(self.api_key)
        self._model = None
        self._robot_service = None
        self._known_people: Dict[str, dict] = {}
        self._face_cascade = None
        self._load_known_people()

        if self.enabled:
            genai.configure(api_key=self.api_key)

    def _get_model(self):
        """Lazy load Gemini model."""
        if self._model is None and self.enabled:
            self._model = genai.GenerativeModel('gemini-2.0-flash')
        return self._model

    def _get_robot_service(self):
        """Lazy load robot service."""
        if self._robot_service is None:
            from .robot_service import robot_service
            self._robot_service = robot_service
        return self._robot_service

    def _get_face_cascade(self):
        """Get OpenCV face cascade classifier."""
        if self._face_cascade is None:
            cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
            self._face_cascade = cv2.CascadeClassifier(cascade_path)
        return self._face_cascade

    def _load_known_people(self):
        """Load known people from storage."""
        people_file = FACES_DIR / "people.json"
        if people_file.exists():
            try:
                with open(people_file, 'r') as f:
                    self._known_people = json.load(f)
            except Exception as e:
                print(f"[Recognition] Failed to load people: {e}")
                self._known_people = {}

    def _save_known_people(self):
        """Save known people to storage."""
        people_file = FACES_DIR / "people.json"
        try:
            with open(people_file, 'w') as f:
                json.dump(self._known_people, f, indent=2)
        except Exception as e:
            print(f"[Recognition] Failed to save people: {e}")

    def is_configured(self) -> bool:
        return self.enabled

    def _decode_image(self, image_base64: str) -> np.ndarray:
        """Decode base64 image to numpy array."""
        img_data = base64.b64decode(image_base64)
        nparr = np.frombuffer(img_data, np.uint8)
        return cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    def _encode_image(self, image: np.ndarray) -> str:
        """Encode numpy array to base64."""
        _, buffer = cv2.imencode('.jpg', image)
        return base64.b64encode(buffer).decode('utf-8')

    async def detect_faces(self, image_base64: str) -> dict:
        """Detect faces in an image using OpenCV."""
        try:
            image = self._decode_image(image_base64)
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

            cascade = self._get_face_cascade()
            faces = cascade.detectMultiScale(
                gray,
                scaleFactor=1.1,
                minNeighbors=5,
                minSize=(30, 30)
            )

            detected_faces = []
            for i, (x, y, w, h) in enumerate(faces):
                # Extract face region
                face_img = image[y:y+h, x:x+w]
                face_base64 = self._encode_image(face_img)

                detected_faces.append({
                    "id": i,
                    "bbox": {"x": int(x), "y": int(y), "w": int(w), "h": int(h)},
                    "face_image": face_base64
                })

            return {
                "success": True,
                "face_count": len(detected_faces),
                "faces": detected_faces
            }

        except Exception as e:
            return {"success": False, "message": str(e)}

    async def recognize_people(self, image_base64: str) -> dict:
        """Recognize and describe people in an image using Gemini."""
        if not self.enabled:
            return {"success": False, "message": "Gemini API not configured"}

        try:
            model = self._get_model()

            # First detect faces
            detection_result = await self.detect_faces(image_base64)

            # Build context about known people
            known_context = ""
            if self._known_people:
                known_context = "\n\nKnown people in database:\n"
                for person_id, person in self._known_people.items():
                    known_context += f"- {person['name']}: {person.get('description', 'No description')}\n"

            # Use Gemini to analyze the image
            prompt = f"""Analyze this image and identify all people visible.
For each person, provide:
1. A brief physical description (clothing, hair, etc.)
2. Estimated age range
3. Current activity or posture
4. If they match any known person from the database, identify them
{known_context}

Respond in JSON format:
{{
    "people": [
        {{
            "position": "left/center/right",
            "description": "brief description",
            "age_range": "estimated age",
            "activity": "what they're doing",
            "matched_name": "name if recognized, null otherwise",
            "confidence": "high/medium/low"
        }}
    ],
    "scene_description": "brief description of the overall scene"
}}"""

            # Decode image for Gemini
            image_data = base64.b64decode(image_base64)

            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: model.generate_content([
                    prompt,
                    {"mime_type": "image/jpeg", "data": image_data}
                ])
            )

            # Parse response
            response_text = response.text
            # Extract JSON from response
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0]
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0]

            result = json.loads(response_text.strip())
            result["success"] = True
            result["face_count"] = detection_result.get("face_count", 0)
            result["face_bboxes"] = [f["bbox"] for f in detection_result.get("faces", [])]

            return result

        except Exception as e:
            print(f"[Recognition] Error: {e}")
            return {"success": False, "message": str(e)}

    async def tag_person(self, name: str, image_base64: str, description: str = "") -> dict:
        """Tag/register a person with their face image."""
        try:
            # Generate unique ID
            person_id = f"person_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{name.lower().replace(' ', '_')}"

            # Detect face in the image
            detection_result = await self.detect_faces(image_base64)
            if not detection_result["success"] or detection_result["face_count"] == 0:
                return {"success": False, "message": "No face detected in image"}

            # Use the first detected face
            face_data = detection_result["faces"][0]

            # Get description from Gemini if not provided
            if not description and self.enabled:
                model = self._get_model()
                image_data = base64.b64decode(image_base64)

                response = await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: model.generate_content([
                        "Describe this person briefly in 2-3 sentences focusing on distinguishing features (hair color, glasses, etc.). Be factual and objective.",
                        {"mime_type": "image/jpeg", "data": image_data}
                    ])
                )
                description = response.text.strip()

            # Save face image
            face_image_path = FACES_DIR / f"{person_id}.jpg"
            face_img_data = base64.b64decode(face_data["face_image"])
            with open(face_image_path, 'wb') as f:
                f.write(face_img_data)

            # Store person info
            self._known_people[person_id] = {
                "name": name,
                "description": description,
                "face_image": str(face_image_path),
                "tagged_at": datetime.now().isoformat(),
                "interactions": []
            }
            self._save_known_people()

            return {
                "success": True,
                "message": f"Tagged {name} successfully",
                "person_id": person_id,
                "description": description
            }

        except Exception as e:
            return {"success": False, "message": str(e)}

    async def get_people(self) -> dict:
        """Get list of all tagged people."""
        people_list = []
        for person_id, person in self._known_people.items():
            people_list.append({
                "id": person_id,
                "name": person["name"],
                "description": person.get("description", ""),
                "tagged_at": person.get("tagged_at", ""),
                "interaction_count": len(person.get("interactions", []))
            })

        return {
            "success": True,
            "count": len(people_list),
            "people": people_list
        }

    async def remove_person(self, person_id: str) -> dict:
        """Remove a tagged person."""
        if person_id not in self._known_people:
            return {"success": False, "message": "Person not found"}

        # Remove face image
        person = self._known_people[person_id]
        face_path = Path(person.get("face_image", ""))
        if face_path.exists():
            face_path.unlink()

        # Remove from database
        del self._known_people[person_id]
        self._save_known_people()

        return {"success": True, "message": f"Removed {person.get('name', person_id)}"}

    async def log_interaction(self, person_id: str, interaction_type: str, notes: str = "") -> dict:
        """Log an interaction with a person."""
        if person_id not in self._known_people:
            return {"success": False, "message": "Person not found"}

        interaction = {
            "timestamp": datetime.now().isoformat(),
            "type": interaction_type,
            "notes": notes
        }

        if "interactions" not in self._known_people[person_id]:
            self._known_people[person_id]["interactions"] = []

        self._known_people[person_id]["interactions"].append(interaction)
        self._save_known_people()

        return {"success": True, "message": "Interaction logged"}

    async def live_recognize(self) -> dict:
        """Capture image from robot and recognize people."""
        robot = self._get_robot_service()

        if not robot.connected:
            return {"success": False, "message": "Robot not connected"}

        # Capture image
        capture_result = await robot.capture_image()
        if not capture_result["success"]:
            return {"success": False, "message": "Failed to capture image"}

        # Recognize people
        return await self.recognize_people(capture_result["image_base64"])


# Singleton instance
person_recognition_service = PersonRecognitionService()
