import unittest

from tools.extract_ota_tuple_from_z2m_log import extract_tuples


class ExtractOtaTupleTests(unittest.TestCase):
    def test_extracts_expected_fields(self):
        text = (
            "debug z2m: Received Zigbee message from 'target-a', type 'commandQueryNextImageRequest', "
            "cluster 'genOta', data '{\"fieldControl\":0,\"fileVersion\":112,\"imageType\":5634,"
            "\"manufacturerCode\":4098}' from endpoint 1 with groupID 0"
        )
        result = extract_tuples(text, "target-a")
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["manufacturer_code"], 0x1002)
        self.assertEqual(result[0]["image_type"], 0x1602)
        self.assertEqual(result[0]["file_version"], 112)

    def test_device_filter(self):
        text = (
            "debug z2m: Received Zigbee message from 'Other', type 'commandQueryNextImageRequest', "
            "cluster 'genOta', data '{\"fieldControl\":0,\"fileVersion\":1,\"imageType\":2,"
            "\"manufacturerCode\":3}' from endpoint 1 with groupID 0"
        )
        self.assertEqual(extract_tuples(text, "target-a"), [])


if __name__ == "__main__":
    unittest.main()
