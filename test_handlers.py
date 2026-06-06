try:
    from handlers import common, konspekt, student_tools, admin, schedule, library, university, channels, grants, quiz, resources
    print("✓ All handlers imported successfully")
except Exception as e:
    print(f"✗ Import error: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
