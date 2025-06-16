#!/usr/bin/env python3

import sys
sys.path.append('.')

try:
    from extensions import db
    print("✅ Extensions imported")
    
    from models.user import User
    print("✅ User model imported")
    
    from models.document import Document
    print("✅ Document model imported")
    
    print("🔄 Testing ContractAnalysis model...")
    from models.contract_analysis import ContractAnalysis
    print("✅ ContractAnalysis model imported successfully!")
    
    print("✅ All models working correctly")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc() 