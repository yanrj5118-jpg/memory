import streamlit.web.cli as stcli
import os, sys, traceback

def resolve_path(path):
    # PyInstaller의 임시 폴더(_MEIPASS) 지원
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, path)
    return os.path.abspath(os.path.join(os.getcwd(), path))

if __name__ == "__main__":
    try:
        # app_ko.py 경로 설정
        app_path = resolve_path("app_ko.py")
        
        if not os.path.exists(app_path):
            print(f"Error: Could not find app_ko.py at {app_path}")
            input("Press Enter to exit...")
            sys.exit(1)
            
        # 스트림릿 실행 인자 설정
        sys.argv = [
            "streamlit",
            "run",
            app_path,
            "--global.developmentMode=false",
        ]
        
        # 스트림릿 실행
        stcli.main()
        
    except Exception as e:
        print("======== ERROR OCCURRED ========")
        traceback.print_exc()
        print("================================")
        input("\nPress Enter to close this window...")
