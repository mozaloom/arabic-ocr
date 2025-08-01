# PaddleOCR backend for text extraction
# Initialize PaddleOCR instance
from paddleocr import PaddleOCR
from pdf2image import convert_from_path
import os
ocr = PaddleOCR(
    use_doc_orientation_classify=False,
    use_doc_unwarping=False,
    use_textline_orientation=False)


# open the pdf file and convert it to images
images = convert_from_path("pdfs/النظام الجزائي لجرائم التزوير.pdf", dpi=300)

# Run OCR inference on a sample image 
result = ocr.predict(
    input=images[0],
    use_gpu=False,
    output_dir="output",
    save_crop_res=True,
    save_crop_res_format="jpg",
    det=True,
    rec=True,
    cls=False,
    drop_score=0.5,
    use_angle_cls=False)

# Visualize the results and save the JSON results
for res in result:
    res.print()
    res.save_to_img("output/output")
    res.save_to_json("output/output.json")
