import json

from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from authors.apps.articles.serializers import ArticleSerializer
from authors.apps.authentication.models import User
from authors.apps.highlights.response_messages import HIGHLIGHT_MSGS
from authors.apps.highlights.utils import remove_highlights_for_article


class TestHighlightViews(TestCase):
    """
    Test the API views used to interact with highlights.
    """

    def setUp(self):
        """
        Add dummy data to test the highlights views.
        """
        self.highlight_data, self.highlight_data2 = None, None
        self.user_data = {
            "username": "test_user",
            "email": "test_user@mailinator.com",
            "password": "P@ssW0rd!"
        }

        self.user = User.objects.create_user(**self.user_data)
        self.article_data = {
            'title': 'the quick brown fox',
            'body': "this article is nice" * 10,
            'description': 'this is a description',
            'author': self.user,
            'tags': []
        }
        self.article_data2 = {
            'title': 'New article data',
            'body': "this article is nice" * 10,
            'description': 'this is a new description',
            'author': self.user,
            'tags': []
        }
        self.update_article = {
            'body': "this article is updated" * 10,
        }
        self.highlight_data = {
            "highlight_data": {
                "start_index": 2,
                "end_index": 8
            }
        }
        self.highlight_data2 = {
            "highlight_data": {
                "start_index": 14,
                "end_index": 24,
                "private": False
            }
        }
        self.article = ArticleSerializer(data=self.article_data)
        self.article.is_valid()
        self.article = self.article.save(author=self.user)
        self.article2 = ArticleSerializer(data=self.article_data2)
        self.article2.is_valid()
        self.article2 = self.article2.save(author=self.user)
        self.user.is_verified = True
        self.user.save()
        self.test_client = APIClient()

    def login_a_user(self):
        """
        Reusable function to login a user
        """
        login_data = {
            "user": {
                "username": self.user_data["username"],
                "email": self.user_data["email"],
                "password": self.user_data["password"]
            }
        }
        response = self.test_client.post(
            "/api/users/login/",
            data=json.dumps(login_data),
            content_type='application/json')
        token = response.json()['user']['token']
        return token

    def create_highlights(self):
        """
        Create highlights for use in testss
        """
        token = self.login_a_user()
        headers = {'HTTP_AUTHORIZATION': 'Bearer ' + token}
        self.test_client.post(
            reverse("highlights:create-get-delete-highlights",
                    kwargs={"slug": self.article.slug}),
            **headers,
            content_type='application/json',
            data=json.dumps(self.highlight_data)
        )
        response = self.test_client.post(
            reverse("highlights:create-get-delete-highlights",
                    kwargs={"slug": self.article.slug}),
            **headers,
            content_type='application/json',
            data=json.dumps(self.highlight_data2)
        )

        return response

    def test_user_can_add_a_highlight(self):
        """
        Test a user can highlight an article's text and make a comment on it
        """
        token = self.login_a_user()
        headers = {'HTTP_AUTHORIZATION': 'Bearer ' + token}
        response = self.test_client.post(
            reverse("highlights:create-get-delete-highlights",
                    kwargs={"slug": self.article.slug}),
            **headers,
            content_type='application/json',
            data=json.dumps(self.highlight_data)
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertEqual(
            HIGHLIGHT_MSGS['HIGHLIGHTED_ADDED'],
            response.data['message'])

    def test_user_can_fetch_their_highlights_for_an_article(self):
        """
        Test user can fetch their highlights for a specific article.
        """
        token = self.login_a_user()
        headers = {'HTTP_AUTHORIZATION': 'Bearer ' + token}
        self.create_highlights()
        response = self.test_client.get(
            reverse("highlights:create-get-delete-highlights",
                    kwargs={"slug": self.article.slug}),
            **headers,
            content_type='application/json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            HIGHLIGHT_MSGS['HIGHLIGHTS_FOUND'],
            response.data['message'])

    def test_user_can_fetch_all_their_highlights(self):
        """
        Test user can fetch all their highlights for a specific article.
        """
        token = self.login_a_user()
        headers = {'HTTP_AUTHORIZATION': 'Bearer ' + token}
        self.create_highlights()
        response = self.test_client.get(
            reverse("highlights:get-all-highlights"),
            **headers,
            content_type='application/json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            HIGHLIGHT_MSGS['HIGHLIGHTS_FOUND'],
            response.data['message'])

    def test_user_can_fetch_all_public_highlights_for_an_article(self):
        """
        Test user can fetch all public highlights for a specific article.
        """
        token = self.login_a_user()
        headers = {'HTTP_AUTHORIZATION': 'Bearer ' + token}
        self.create_highlights()
        response = self.test_client.get(
            reverse("highlights:get-all-public-highlights",
                    kwargs={"slug": self.article.slug}),
            **headers,
            content_type='application/json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            HIGHLIGHT_MSGS['PUBLIC_HIGHLIGHTS_FOUND'],
            response.data['message'])

        self.test_client.post(
            reverse("highlights:create-get-delete-highlights",
                    kwargs={"slug": self.article.slug}),
            **headers,
            content_type='application/json',
            data=json.dumps(self.highlight_data2)
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_404 = self.test_client.get(
            reverse("highlights:get-all-public-highlights",
                    kwargs={"slug": self.article.slug}),
            **headers,
            content_type='application/json'
        )
        self.assertEqual(response_404.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(
            HIGHLIGHT_MSGS['NO_PUBLIC_HIGHLIGHTS'],
            response_404.data['errors'])
        response = self.test_client.get(
            reverse("highlights:get-all-public-highlights",
                    kwargs={"slug": 'fake-slug'}),
            **headers,
            content_type='application/json'
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(
            HIGHLIGHT_MSGS['ARTICLE_NOT_FOUND'],
            response.data['errors'])

    def test_user_gets_empty_list_if_they_have_no_highlights(self):
        """
        Test user gets empty list if they have no highlights for a specific article.
        """
        token = self.login_a_user()
        headers = {'HTTP_AUTHORIZATION': 'Bearer ' + token}
        response = self.test_client.get(
            reverse("highlights:create-get-delete-highlights",
                    kwargs={"slug": self.article.slug}),
            **headers,
            content_type='application/json'
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(
            HIGHLIGHT_MSGS['NO_HIGHLIGHTS'],
            response.data['errors'])

    def test_user_can_delete_a_highlight(self):
        """
        Test a user can delete highlight they created
        """
        token = self.login_a_user()
        headers = {'HTTP_AUTHORIZATION': 'Bearer ' + token}
        self.create_highlights()
        response = self.test_client.post(
            reverse("highlights:create-get-delete-highlights",
                    kwargs={"slug": self.article.slug}),
            **headers,
            content_type='application/json',
            data=json.dumps(self.highlight_data)
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            HIGHLIGHT_MSGS['HIGHLIGHT_REMOVED'],
            response.data['message'])

    def test_user_cannot_create_a_highlight_if_article_doesnot_exist(self):
        """
        Test a user cannot create a highlight if an article does not exist
        """
        token = self.login_a_user()
        headers = {'HTTP_AUTHORIZATION': 'Bearer ' + token}
        response = self.test_client.post(
            reverse("highlights:create-get-delete-highlights",
                    kwargs={"slug": 'fake-slug'}),
            **headers,
            content_type='application/json',
            data=json.dumps(self.highlight_data)
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        self.assertEqual(
            HIGHLIGHT_MSGS['ARTICLE_NOT_FOUND'],
            response.data['errors'])

    def test_user_update_a_highlight_comment_or_privacy(self):
        """
        Test a user can update a highlight's comment
        """
        token = self.login_a_user()
        headers = {'HTTP_AUTHORIZATION': 'Bearer ' + token}
        highlight_data = {
            "highlight_data": {
                "comment": "updated comment",
                "private": False,
            }
        }
        res = self.create_highlights()
        highlight_id = res.data['highlight']['id']
        response = self.test_client.patch(
            reverse("highlights:update-highlights",
                    kwargs={"pk": highlight_id}),
            **headers,
            content_type='application/json',
            data=json.dumps(highlight_data)
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            HIGHLIGHT_MSGS['HIGHLIGHT_UPDATED'],
            response.data['message'])
        self.assertFalse(response.data['highlight']['private'])
        response = self.test_client.patch(
            reverse("highlights:update-highlights",
                    kwargs={"pk": highlight_id}),
            **headers,
            content_type='application/json',
            data=json.dumps(highlight_data)
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_user_cannot_update_a_highlight_without_new_comment_or_privacy(self):
        """
        Test a user can update a highlight's comment
        """
        token = self.login_a_user()
        headers = {'HTTP_AUTHORIZATION': 'Bearer ' + token}
        highlight_data = {
            "highlight_data": {
            }
        }
        res = self.create_highlights()
        highlight_id = res.data['highlight']['id']
        response = self.test_client.patch(
            reverse("highlights:update-highlights",
                    kwargs={"pk": highlight_id}),
            **headers,
            content_type='application/json',
            data=json.dumps(highlight_data)
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            HIGHLIGHT_MSGS['HIGHLIGHTS_COMMENT_OR_PRIVATE_FIELD_REQUIRED'],
            response.data['errors'])

    def test_user_cannot_update_a_highlight_comment_if_highlight_is_nonexistent(self):
        """
        Test a user cannot update a non-existent highlight's comment
        """
        token = self.login_a_user()
        headers = {'HTTP_AUTHORIZATION': 'Bearer ' + token}
        highlight_data = {
            "highlight_data": {
                "comment": "updated comment"
            }
        }
        res = self.create_highlights()
        highlight_id = res.data['highlight']['id']
        response = self.test_client.patch(
            reverse("highlights:update-highlights",
                    kwargs={"pk": 10000}),
            **headers,
            content_type='application/json',
            data=json.dumps(highlight_data)
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(
            HIGHLIGHT_MSGS['HIGHLIGHTS_NOT_FOUND'],
            response.data['errors'])

    def test_user_cannot_fetch_a_highlight_if_article_doesnot_exist(self):
        """
        Test a user cannot create a highlight if an article does not exist
        """
        token = self.login_a_user()
        headers = {'HTTP_AUTHORIZATION': 'Bearer ' + token}
        response = self.test_client.get(
            reverse("highlights:create-get-delete-highlights",
                    kwargs={"slug": 'fake-slug'}),
            **headers,
            content_type='application/json'
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        self.assertEqual(
            HIGHLIGHT_MSGS['ARTICLE_NOT_FOUND'],
            response.data['errors'])

    def test_if_we_can_delete_all_highlights_for_an_article(self):
        """
        Test if we can delete the highlights made for an article
        Using the utility function remove_highlights_for_article
        :return:
        """
        self.create_highlights()
        self.assertTrue(remove_highlights_for_article(self.article))

    def test_highlights_cannot_be_deleted_for_an_article_if_they_dont_exist(self):
        """
        Test if we return None if there are no highlights made for an article hence nothing to delete
        Using the utility function remove_highlights_for_article
        :return:
        """
        self.assertIsNone(remove_highlights_for_article(self.article))

    def test_highlights_get_deleted_if_article_body_is_updated(self):
        """
        Test if the highlights for an article get removed
        Should the author update the articles
        :return:
        """
        self.create_highlights()
        token = self.login_a_user()
        headers = {'HTTP_AUTHORIZATION': 'Bearer ' + token}
        response1 = self.test_client.put(
            reverse("articles:article",
                    kwargs={"slug": self.article.slug}),
            **headers,
            content_type='application/json',
            data=json.dumps(self.update_article)
        )
        self.assertEqual(response1.status_code, status.HTTP_200_OK)
        self.assertIsNone(remove_highlights_for_article(self.article))
