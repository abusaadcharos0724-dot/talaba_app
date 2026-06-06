import os
from utils.pptx_gen import create_presentation_pptx

TEST_OUTPUT = "test_template_output.pptx"
TEMPLATE_PATH = "data/templates/default.pptx"

def test():
    # 1. Clean up existing template to test auto-gen
    if os.path.exists(TEMPLATE_PATH):
        try:
            os.remove(TEMPLATE_PATH)
            print("Removed existing template.")
        except:
            pass

    # 2. Generate presentation (should trigger template gen)
    print("Generating presentation...")
    content = "||| Title Slide\nThis is a test.\n||| Slide 2\nContent here."
    create_presentation_pptx("Template Test", content, TEST_OUTPUT)
    
    # 3. Check if template exists
    if os.path.exists(TEMPLATE_PATH):
        print("SUCCESS: Standard template auto-generated.")
    else:
        print("FAILURE: Template not generated.")
        
    # 4. Check output
    if os.path.exists(TEST_OUTPUT):
        print(f"SUCCESS: Presentation created at {TEST_OUTPUT}")
    else:
        print("FAILURE: Presentation not created.")

if __name__ == "__main__":
    test()
