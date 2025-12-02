"""
DrugFood Guard - Database Module
사용자 약물 등록 및 조회를 위한 SQLite 데이터베이스 관리
"""
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
import sys

# 상위 디렉토리를 path에 추가
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

try:
    from app.config import SQLITE_DB_PATH
except ImportError:
    # 직접 실행 시
    SQLITE_DB_PATH = str(Path(__file__).parent.parent.parent / "data" / "drugfood.db")


class UserDrugDB:
    """사용자 약물 데이터베이스 관리 클래스"""
    
    def __init__(self, db_path: str = SQLITE_DB_PATH):
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        """데이터베이스 및 테이블 초기화"""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 사용자 테이블 (인증 정보 추가)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY,
                email TEXT,
                name TEXT,
                password TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 기존 테이블에 컬럼이 없는 경우 추가 (마이그레이션)
        try:
            cursor.execute("ALTER TABLE users ADD COLUMN email TEXT")
        except sqlite3.OperationalError:
            pass
        try:
            cursor.execute("ALTER TABLE users ADD COLUMN name TEXT")
        except sqlite3.OperationalError:
            pass
        try:
            cursor.execute("ALTER TABLE users ADD COLUMN password TEXT")
        except sqlite3.OperationalError:
            pass
        
        # 사용자 등록 약물 테이블
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_drugs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                drug_name TEXT NOT NULL,
                drug_ingredient TEXT,
                drug_category TEXT,
                dosage TEXT,
                notes TEXT,
                registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id),
                UNIQUE(user_id, drug_name)
            )
        """)
        
        # 상호작용 조회 기록 테이블
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS query_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                query_text TEXT NOT NULL,
                response_text TEXT,
                queried_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """)
        
        conn.commit()
        conn.close()
    
    def _get_connection(self):
        """데이터베이스 연결 반환"""
        return sqlite3.connect(self.db_path)
    
    # ===== 사용자 관리 =====
    def create_user(self, user_id: str, email: str = None, name: str = None, password: str = None) -> bool:
        """새 사용자 생성 (회원가입)"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # 이미 존재하는지 확인
            cursor.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,))
            if cursor.fetchone():
                # 업데이트 (비밀번호 등)
                cursor.execute("""
                    UPDATE users 
                    SET email = COALESCE(?, email),
                        name = COALESCE(?, name),
                        password = COALESCE(?, password),
                        updated_at = CURRENT_TIMESTAMP
                    WHERE user_id = ?
                """, (email, name, password, user_id))
            else:
                # 신규 생성
                cursor.execute(
                    "INSERT INTO users (user_id, email, name, password) VALUES (?, ?, ?, ?)",
                    (user_id, email, name, password)
                )
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error creating/updating user: {e}")
            return False
    
    def get_user(self, user_id: str) -> Optional[Dict]:
        """사용자 정보 조회"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT user_id, email, name, password, created_at, updated_at FROM users WHERE user_id = ?",
            (user_id,)
        )
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                "user_id": row[0],
                "email": row[1],
                "name": row[2],
                "password": row[3],
                "created_at": row[4],
                "updated_at": row[5]
            }
        return None

    def get_all_users(self) -> Dict[str, Dict]:
        """모든 사용자 정보 조회 (Streamlit Authenticator 포맷)"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT user_id, email, name, password FROM users WHERE password IS NOT NULL")
        rows = cursor.fetchall()
        conn.close()
        
        users_dict = {}
        for row in rows:
            users_dict[row[0]] = {
                "email": row[1],
                "name": row[2],
                "password": row[3]
            }
        return users_dict
    
    # ===== 약물 등록 관리 =====
    def register_drug(
        self,
        user_id: str,
        drug_name: str,
        drug_ingredient: str = None,
        drug_category: str = None,
        dosage: str = None,
        notes: str = None
    ) -> Dict:
        """사용자 약물 등록"""
        # 사용자가 없으면 생성
        self.create_user(user_id)
        
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT OR REPLACE INTO user_drugs 
                (user_id, drug_name, drug_ingredient, drug_category, dosage, notes)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (user_id, drug_name, drug_ingredient, drug_category, dosage, notes))
            
            conn.commit()
            conn.close()
            
            return {
                "success": True,
                "message": f"'{drug_name}' 약물이 등록되었습니다.",
                "drug_name": drug_name
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"약물 등록 실패: {str(e)}",
                "drug_name": drug_name
            }
    
    def remove_drug(self, user_id: str, drug_name: str) -> Dict:
        """사용자 약물 삭제"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                DELETE FROM user_drugs 
                WHERE user_id = ? AND drug_name = ?
            """, (user_id, drug_name))
            
            affected = cursor.rowcount
            conn.commit()
            conn.close()
            
            if affected > 0:
                return {
                    "success": True,
                    "message": f"'{drug_name}' 약물이 삭제되었습니다."
                }
            else:
                return {
                    "success": False,
                    "message": f"'{drug_name}' 약물을 찾을 수 없습니다."
                }
        except Exception as e:
            return {
                "success": False,
                "message": f"약물 삭제 실패: {str(e)}"
            }
    
    def get_user_drugs(self, user_id: str) -> List[Dict]:
        """사용자의 등록된 약물 목록 조회"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT drug_name, drug_ingredient, drug_category, dosage, notes, registered_at
            FROM user_drugs
            WHERE user_id = ?
            ORDER BY registered_at DESC
        """, (user_id,))
        
        rows = cursor.fetchall()
        conn.close()
        
        drugs = []
        for row in rows:
            drugs.append({
                "drug_name": row[0],
                "drug_ingredient": row[1],
                "drug_category": row[2],
                "dosage": row[3],
                "notes": row[4],
                "registered_at": row[5]
            })
        
        return drugs
    
    def get_user_drug_names(self, user_id: str) -> List[str]:
        """사용자의 등록된 약물 이름만 조회"""
        drugs = self.get_user_drugs(user_id)
        return [drug["drug_name"] for drug in drugs]
    
    def clear_user_drugs(self, user_id: str) -> Dict:
        """사용자의 모든 약물 삭제"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute(
                "DELETE FROM user_drugs WHERE user_id = ?",
                (user_id,)
            )
            
            affected = cursor.rowcount
            conn.commit()
            conn.close()
            
            return {
                "success": True,
                "message": f"{affected}개의 약물이 삭제되었습니다."
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"약물 삭제 실패: {str(e)}"
            }
    
    # ===== 조회 기록 관리 =====
    def save_query(self, user_id: str, query_text: str, response_text: str = None):
        """질문 기록 저장"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO query_history (user_id, query_text, response_text)
                VALUES (?, ?, ?)
            """, (user_id, query_text, response_text))
            
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Error saving query: {e}")
    
    def get_query_history(self, user_id: str, limit: int = 10) -> List[Dict]:
        """질문 기록 조회"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT query_text, response_text, queried_at
            FROM query_history
            WHERE user_id = ?
            ORDER BY queried_at DESC
            LIMIT ?
        """, (user_id, limit))
        
        rows = cursor.fetchall()
        conn.close()
        
        history = []
        for row in rows:
            history.append({
                "query": row[0],
                "response": row[1],
                "timestamp": row[2]
            })
        
        return history


# 테스트 코드
if __name__ == "__main__":
    db = UserDrugDB()
    
    # 테스트 사용자 생성
    test_user = "test_user_001"
    db.create_user(test_user)
    
    # 약물 등록 테스트
    result = db.register_drug(
        user_id=test_user,
        drug_name="암로디핀",
        drug_ingredient="암로디핀베실산염",
        drug_category="혈압약",
        dosage="5mg 1일 1회"
    )
    print(f"등록 결과: {result}")
    
    result = db.register_drug(
        user_id=test_user,
        drug_name="메트포르민",
        drug_ingredient="메트포르민염산염",
        drug_category="당뇨약",
        dosage="500mg 1일 2회"
    )
    print(f"등록 결과: {result}")
    
    # 약물 목록 조회
    drugs = db.get_user_drugs(test_user)
    print(f"\n등록된 약물 ({len(drugs)}개):")
    for drug in drugs:
        print(f"  - {drug['drug_name']} ({drug['drug_category']})")
    
    # 약물 이름만 조회
    drug_names = db.get_user_drug_names(test_user)
    print(f"\n약물 이름 목록: {drug_names}")
