"""
Script to test API endpoints
Run: python scripts/test_api.py
"""

import requests
import json
from datetime import date, datetime

BASE_URL = 'http://localhost:8000/api'

class APITester:
    def __init__(self):
        self.base_url = BASE_URL
        self.token = None
        
    def print_response(self, response, title="Response"):
        """Pretty print response"""
        print(f"\n{'='*60}")
        print(f"{title}")
        print(f"{'='*60}")
        print(f"Status Code: {response.status_code}")
        print(f"Response:")
        try:
            print(json.dumps(response.json(), indent=2, ensure_ascii=False))
        except:
            print(response.text)
        print(f"{'='*60}\n")
    
    def login(self, username='admin', password='admin123'):
        """Test login"""
        print("\n🔐 Testing Login...")
        url = f"{self.base_url}/auth/login/"
        data = {
            "username": username,
            "password": password
        }
        
        response = requests.post(url, json=data)
        self.print_response(response, "Login Response")
        
        if response.status_code == 200:
            result = response.json()
            self.token = result['tokens']['access']
            print(f"✓ Login successful! Token: {self.token[:50]}...")
            return True
        else:
            print("✗ Login failed!")
            return False
    
    def get_headers(self):
        """Get headers with auth token"""
        return {
            'Authorization': f'Bearer {self.token}',
            'Content-Type': 'application/json'
        }
    
    def test_get_users(self):
        """Test get users list"""
        print("\n👥 Testing Get Users...")
        url = f"{self.base_url}/auth/users/"
        
        response = requests.get(url, headers=self.get_headers())
        self.print_response(response, "Users List")
        
        return response.status_code == 200
    
    def test_get_profile(self):
        """Test get user profile"""
        print("\n👤 Testing Get Profile...")
        url = f"{self.base_url}/auth/profile/"
        
        response = requests.get(url, headers=self.get_headers())
        self.print_response(response, "User Profile")
        
        return response.status_code == 200
    
    def test_get_classes(self):
        """Test get classes"""
        print("\n🏫 Testing Get Classes...")
        url = f"{self.base_url}/students/classes/"
        
        response = requests.get(url, headers=self.get_headers())
        self.print_response(response, "Classes List")
        
        return response.status_code == 200
    
    def test_get_students(self):
        """Test get students"""
        print("\n👦 Testing Get Students...")
        url = f"{self.base_url}/students/students/"
        
        response = requests.get(url, headers=self.get_headers())
        self.print_response(response, "Students List")
        
        return response.status_code == 200
    
    def test_get_vehicles(self):
        """Test get vehicles"""
        print("\n🚌 Testing Get Vehicles...")
        url = f"{self.base_url}/routes/vehicles/"
        
        response = requests.get(url, headers=self.get_headers())
        self.print_response(response, "Vehicles List")
        
        return response.status_code == 200
    
    def test_get_routes(self):
        """Test get routes"""
        print("\n🗺️  Testing Get Routes...")
        url = f"{self.base_url}/routes/routes/"
        
        response = requests.get(url, headers=self.get_headers())
        self.print_response(response, "Routes List")
        
        return response.status_code == 200
    
    def test_get_trips(self):
        """Test get trips"""
        print("\n🚗 Testing Get Trips...")
        url = f"{self.base_url}/tracking/trips/"
        
        response = requests.get(url, headers=self.get_headers())
        self.print_response(response, "Trips List")
        
        return response.status_code == 200
    
    def test_create_class(self):
        """Test create class"""
        print("\n➕ Testing Create Class...")
        url = f"{self.base_url}/students/classes/"
        
        data = {
            "name": "Test Class",
            "grade_level": 5,
            "academic_year": "2024-2025",
            "teacher_name": "Test Teacher",
            "is_active": True
        }
        
        response = requests.post(url, json=data, headers=self.get_headers())
        self.print_response(response, "Create Class Response")
        
        return response.status_code == 201
    
    def test_api_documentation(self):
        """Test API documentation access"""
        print("\n📚 Testing API Documentation...")
        url = f"http://localhost:8000/swagger/"
        
        try:
            response = requests.get(url)
            if response.status_code == 200:
                print("✓ Swagger documentation is accessible")
                return True
            else:
                print("✗ Swagger documentation not accessible")
                return False
        except Exception as e:
            print(f"✗ Error accessing documentation: {e}")
            return False
    
    def run_all_tests(self):
        """Run all tests"""
        print("\n" + "="*60)
        print("STARTING API TESTS")
        print("="*60)
        
        results = {}
        
        # Login first
        if not self.login():
            print("\n❌ Login failed! Cannot proceed with other tests.")
            return
        
        # Run tests
        tests = [
            ("Get Profile", self.test_get_profile),
            ("Get Users", self.test_get_users),
            ("Get Classes", self.test_get_classes),
            ("Get Students", self.test_get_students),
            ("Get Vehicles", self.test_get_vehicles),
            ("Get Routes", self.test_get_routes),
            ("Get Trips", self.test_get_trips),
            ("Create Class", self.test_create_class),
            ("API Documentation", self.test_api_documentation),
        ]
        
        for test_name, test_func in tests:
            try:
                results[test_name] = test_func()
            except Exception as e:
                print(f"\n❌ Error in {test_name}: {e}")
                results[test_name] = False
        
        # Print summary
        print("\n" + "="*60)
        print("TEST SUMMARY")
        print("="*60)
        
        passed = sum(1 for v in results.values() if v)
        total = len(results)
        
        for test_name, result in results.items():
            status = "✓ PASS" if result else "✗ FAIL"
            print(f"{status:10} | {test_name}")
        
        print(f"\n{'='*60}")
        print(f"Results: {passed}/{total} tests passed")
        print(f"{'='*60}\n")
        
        return passed == total

def main():
    """Main function"""
    tester = APITester()
    success = tester.run_all_tests()
    
    if success:
        print("🎉 All tests passed!")
    else:
        print("⚠️  Some tests failed. Check the output above.")

if __name__ == '__main__':
    main()