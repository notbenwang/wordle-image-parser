import unittest
from automation import image_to_text, get_box_points, correct_box_points, filename_to_image
from wordle_config import Config

class TestAutomationMethods(unittest.TestCase):
    config = Config()
    def test_config_setup(self):
        self.assertEqual(len(self.config.word_bank),14855)

    # 2 next tests currently removed because involves installing pytesseract cmd on github actions, which is a bit annoying for me
    # If anyone wants to figure out how to do that for me, that would be awesome

    # def test_image_to_text_standard(self):
    #     img = filename_to_image('wordle_images/image_108.jpg')
    #     _,text,_ = image_to_text(img)
    #     self.assertEqual(len(text),3)
    #     self.assertEqual(text[0],"BOARD")
    #     self.assertEqual(text[1],"FLOOD")
    #     self.assertEqual(text[2],"SCOLD")

    # def test_image_to_text_case1(self):
    #     # Bad Crop
    #     img = filename_to_image('wordle_images/image_886.jpg')
    #     _,text,_ = image_to_text(img)
    #     self.assertEqual(len(text),6)
    #     self.assertEqual(text[0],"AZURE")
    #     self.assertEqual(text[1],"STAND")
    #     self.assertEqual(text[2],"BALDY")
    #     self.assertEqual(text[3],"MADDY")
    #     self.assertEqual(text[4],"PADDY")
    #     self.assertEqual(text[5],"DADDY")

    def test_get_box_points_standard(self):
        img = filename_to_image('wordle_images/image_730.jpg')
        points, _, _ =  get_box_points(img)
        self.assertEqual(len(points), 30)
    
    def test_correct_box_points_less_than_30(self):
        img = filename_to_image('wordle_images/image_29.jpg')
        points, _, _ = get_box_points(img)
        points = correct_box_points(points)
        self.assertEqual(len(points), 30)


if __name__ == '__main__':
    unittest.main()