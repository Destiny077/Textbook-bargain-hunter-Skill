import unittest

from src.optimizer import run_optimizer


class CandidateIsolationTests(unittest.TestCase):
    def make_book(self, title, price, condition='A', **metadata):
        return dict(
            book=title,
            candidates=[{
                'platform': '孔夫子',
                'shop': title + '店铺',
                'title': title + '商品',
                'url': 'https://example.com/books/' + str(price),
                'price': price,
                'shipping': 0,
                'internal_condition': condition,
                'edition_match': 'exact',
            }],
            **metadata
        )

    def assert_isolated(self, books):
        result = run_optimizer(books)
        self.assertEqual(set(result['plans']), {'cheapest', 'balanced', 'quality'})
        for strategy, plan in result['plans'].items():
            with self.subTest(strategy=strategy):
                self.assertEqual(len(plan['items']), len(books))
                for book, item in zip(books, plan['items']):
                    self.assertEqual(item['book_title'], book['book'])
                    self.assertEqual(item['book_isbn'], book.get('isbn', ''))
                    self.assertIn(item['url'], [c['url'] for c in book['candidates']])
                self.assertEqual(plan['total_price'], 30)

    def test_empty_isbns_do_not_share_candidates(self):
        self.assert_isolated([
            self.make_book('Book A', 10, isbn=''),
            self.make_book('Book B', 20, isbn=''),
        ])

    def test_missing_isbns_do_not_share_candidates(self):
        self.assert_isolated([
            self.make_book('Book A', 10),
            self.make_book('Book B', 20),
        ])

    def test_mixed_missing_and_empty_isbns_do_not_share_candidates(self):
        self.assert_isolated([
            self.make_book('Book A', 10, isbn=''),
            self.make_book('Book B', 20),
        ])

    def test_same_titles_without_isbns_do_not_share_candidates(self):
        self.assert_isolated([
            self.make_book('Same title', 10),
            self.make_book('Same title', 20),
        ])

    def test_repeated_isbns_do_not_overwrite_candidates(self):
        self.assert_isolated([
            self.make_book('Book A', 10, isbn='9787302147510'),
            self.make_book('Book B', 20, isbn='9787302147510'),
        ])

    def test_distinct_isbns_keep_existing_behavior(self):
        self.assert_isolated([
            self.make_book('Book A', 10, isbn='9787302147510'),
            self.make_book('Book B', 20, isbn='9787040396638'),
        ])

    def test_unavailable_reason_uses_each_books_own_candidates(self):
        for metadata in ({}, {'isbn': ''}):
            with self.subTest(metadata=metadata):
                books = [
                    self.make_book('Book A', 10, condition='B', **metadata),
                    self.make_book('Book B', 20, **metadata),
                ]
                result = run_optimizer(books, 'quality')
                self.assertEqual(result['plans'], {})
                self.assertEqual(result['meta']['strategies_unavailable']['quality'], [
                    'Book A: 无满足品相要求的候选 (共1个候选)',
                ])

    def test_missing_candidates_are_not_replaced_by_another_books(self):
        books = [
            {'book': 'Book A', 'isbn': '', 'candidates': []},
            self.make_book('Book B', 20, isbn=''),
        ]
        result = run_optimizer(books, 'cheapest')
        self.assertEqual(result['plans'], {})
        self.assertEqual(result['meta']['strategies_unavailable']['cheapest'], [
            'Book A: 无候选商品',
        ])


if __name__ == '__main__':
    unittest.main()
