"""
Complete Setup Script
Run this to set up everything in correct order
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent))

from config.settings import (
    get_config_summary, 
    validate_paths,
    PDF_PATH,
    PATIENT_DB_PATH,
    VECTOR_DB_PATH
)


def print_header(text):
    """Print formatted header"""
    print("\n" + "="*70)
    print(f"  {text}")
    print("="*70 + "\n")


def check_prerequisites():
    """Check if all prerequisites are met"""
    print_header("CHECKING PREREQUISITES")
    
    issues = []
    
    # Check Python version
    if sys.version_info < (3, 9):
        issues.append("❌ Python 3.9+ required")
    else:
        print(f"✅ Python version: {sys.version.split()[0]}")
    
    # Check required packages
    required_packages = [
        "langchain",
        "groq", 
        "chromadb",
        "sentence_transformers",
        "streamlit",
        "pypdf",
        "pandas",
        "faker"
    ]
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"✅ {package}: Installed")
        except ImportError:
            issues.append(f"❌ {package}: NOT INSTALLED")
            print(f"❌ {package}: NOT INSTALLED")
    
    # Check API keys
    from config.settings import GROQ_API_KEY, TAVILY_API_KEY
    
    if GROQ_API_KEY:
        print("✅ GROQ_API_KEY: Set")
    else:
        issues.append("❌ GROQ_API_KEY: NOT SET in .env")
        print("❌ GROQ_API_KEY: NOT SET")
    
    if TAVILY_API_KEY:
        print("✅ TAVILY_API_KEY: Set")
    else:
        print("⚠️  TAVILY_API_KEY: NOT SET (web search limited)")
    
    return issues


def setup_step_1_patient_data():
    """Generate patient data"""
    print_header("STEP 1: GENERATING PATIENT DATA")
    
    if PATIENT_DB_PATH.exists():
        print("✅ Patient database already exists!")
        response = input("   Re-generate patient data? (yes/no): ")
        if response.lower() != 'yes':
            return
    
    try:
        from src.data_preparation.patient_data_generator import (
            generate_all_patients,
            save_to_json,
            save_to_sqlite
        )
        
        print("🔄 Generating 30 patient reports...")
        patients = generate_all_patients(num_patients=30)
        
        save_to_json(patients)
        save_to_sqlite(patients)
        
        print("✅ Patient data generated successfully!")
        
    except Exception as e:
        print(f"❌ Error generating patient data: {e}")
        raise


def setup_step_2_pdf_processing():
    """Process PDF and create vector store"""
    print_header("STEP 2: PROCESSING NEPHROLOGY PDF")
    
    # Check if PDF exists
    if not PDF_PATH.exists():
        print(f"❌ PDF not found: {PDF_PATH}")
        print("\nPlease ensure the PDF is at:")
        print(f"   {PDF_PATH}")
        return False
    
    print(f"📖 PDF found: {PDF_PATH}")
    
    # Check if already processed
    vector_db_file = VECTOR_DB_PATH / "chroma.sqlite3"
    
    if vector_db_file.exists():
        print("✅ Vector database already exists!")
        response = input("   Re-process PDF? This takes 20-30 minutes. (yes/no): ")
        if response.lower() != 'yes':
            return True
    
    try:
        from src.data_preparation.pdf_processor import NephrologyPDFProcessor
        
        print("\n🔄 Starting PDF processing...")
        print("⏳ This will take 20-30 minutes for 1547 pages...")
        print("☕ Good time for a coffee break!\n")
        
        processor = NephrologyPDFProcessor(str(PDF_PATH))
        processor.process_full_pipeline()
        
        print("\n✅ PDF processing complete!")
        return True
        
    except Exception as e:
        print(f"❌ Error processing PDF: {e}")
        import traceback
        traceback.print_exc()
        return False


def setup_step_3_test_rag():
    """Test RAG retrieval"""
    print_header("STEP 3: TESTING RAG RETRIEVAL")
    
    try:
        from src.data_preparation.pdf_processor import NephrologyPDFProcessor
        
        processor = NephrologyPDFProcessor(str(PDF_PATH))
        
        test_queries = [
            "What is chronic kidney disease?",
            "Treatment for diabetic nephropathy",
            "Symptoms of acute kidney injury"
        ]
        
        for query in test_queries:
            print(f"\n🔍 Query: '{query}'")
            results = processor.test_retrieval(query, top_k=2)
            print("✅ Retrieval successful!")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing RAG: {e}")
        return False


def main():
    """Main setup flow"""
    
    print("""
    ╔═══════════════════════════════════════════════════════════════╗
    ║                                                               ║
    ║    POST-DISCHARGE MEDICAL AI ASSISTANT - SETUP WIZARD        ║
    ║                                                               ║
    ╚═══════════════════════════════════════════════════════════════╝
    """)
    
    print("\nThis wizard will set up your project step by step.")
    print("Total time: ~30-40 minutes (mostly PDF processing)\n")
    
    input("Press Enter to begin setup...")
    
    # Check prerequisites
    issues = check_prerequisites()
    
    if issues:
        print("\n❌ SETUP CANNOT CONTINUE")
        print("\nPlease fix these issues first:")
        for issue in issues:
            print(f"   {issue}")
        print("\nAfter fixing, run this script again.")
        return
    
    print("\n✅ All prerequisites met!")
    
    # Step 1: Patient Data
    try:
        setup_step_1_patient_data()
    except Exception as e:
        print(f"\n❌ Setup failed at Step 1: {e}")
        return
    
    # Step 2: PDF Processing
    try:
        pdf_success = setup_step_2_pdf_processing()
        if not pdf_success:
            print("\n⚠️  PDF processing skipped or failed")
            print("You can run it later with:")
            print("   python src/data_preparation/pdf_processor.py")
    except Exception as e:
        print(f"\n❌ Setup failed at Step 2: {e}")
        return
    
    # Step 3: Test RAG
    if pdf_success:
        try:
            setup_step_3_test_rag()
        except Exception as e:
            print(f"\n⚠️  RAG testing failed: {e}")
    
    # Final summary
    print_header("SETUP COMPLETE!")
    
    print(get_config_summary())
    
    print("\n📊 Setup Status:")
    print("   ✅ Patient data (30 reports)")
    print("   ✅ SQLite database")
    print(f"   {'✅' if pdf_success else '⚠️ '} PDF processed & vector store")
    
    print("\n🚀 Next Steps:")
    print("   1. Develop agents (Receptionist & Clinical)")
    print("   2. Create LangGraph orchestration")
    print("   3. Build Streamlit frontend")
    print("   4. Test end-to-end workflow")
    
    print("\n💻 To run the app (once complete):")
    print("   streamlit run frontend/streamlit_app.py")
    
    print("\n" + "="*70)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Setup cancelled by user")
    except Exception as e:
        print(f"\n❌ Setup failed: {e}")
        import traceback
        traceback.print_exc()


