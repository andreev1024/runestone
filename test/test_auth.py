__author__ = 'isaacdontjelindell'

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.action_chains import ActionChains
import string
import random
import time

import unittest


def generate_name():
    lst = [random.choice(string.ascii_letters) for n in xrange(20)]
    return "".join(lst)


def generate_email():
    return generate_name() + "@testing.com"


class LocalAuthTests(unittest.TestCase):
    def setUp(self):
        self.username = generate_name()
        self.first_name = generate_name()
        self.last_name = generate_name()
        self.email = generate_email()
        self.password = 't3stp4ssword'
        self.course_name = 'devcourse'
        self.host = 'http://127.0.0.1:8000'

        self.driver = webdriver.Firefox()

    def test_local_auth(self):
        '''
         1. register a new user.
         2. make sure we can log out and log back in as the new user
         3. make sure we can access the profile page for that user
         4. create a new course with that user as the instructor
        '''
        self.register_local()
        self.logout()

        # verify we can login and are redirected to the correct course
        self.login_local()

        # verify the profile page works
        self.profile()

        # make sure the new course designer works
        self.build_new_course_from_existing_course()

        # next 2 steps will verify the new course got created properly
        self.logout()
        self.login_local() # verifies redirection to new course

        self.save_load_activecode()

        self.logout()

    def tearDown(self):
        self.driver.quit()

    ##############################################################################################

    def register_local(self):
        '''
        Use the local web2py authentication to register a new user (info
        generated by setUp()) Once the user is registered, confirm that
        they are redirected to the course they registered for.
        '''
        self.driver.get(self.host + '/runestone/default/user/register')

        ## fill out the registration form ##
        self.driver.find_element_by_id('auth_user_username'). \
            send_keys(self.username)
        self.driver.find_element_by_id('auth_user_first_name'). \
            send_keys(self.first_name)
        self.driver.find_element_by_id('auth_user_last_name'). \
            send_keys(self.last_name)
        self.driver.find_element_by_id('auth_user_email'). \
            send_keys(self.email)
        self.driver.find_element_by_id('auth_user_password'). \
            send_keys(self.password)
        self.driver.find_element_by_name('password_two'). \
            send_keys(self.password)
        self.driver.find_element_by_id('auth_user_course_id'). \
            send_keys(self.course_name)

        ## wait until the Captcha has been filled and we navigate away ##
        #element = self.driver.find_element_by_id('auth_user_username')
        #WebDriverWait(self.driver, 20).until(EC.staleness_of(element))

        ## submit the registration form ##
        self.driver.find_element_by_css_selector("input[value='Register']"). \
            click()

        ## check for errors in the registration form ##
        try:
            form_error = self.driver.find_element_by_class_name('error').text
            self.assertRaises(RuntimeError("Error in registration form: %s" % form_error))
        except NoSuchElementException:
            pass

        ## check that we were redirected to the course we just registered for ##
        expected_course_url = self.host + "/runestone/static/" + self.course_name
        self.assertIn(expected_course_url, self.driver.current_url,
                      "Newly registered user not redirected to expected course (%s)." % self.course_name)

    def login_local(self):
        '''
        Verify that we can use local web2py auth to log in (with the user account
        that was created in register())
        '''

        self.driver.get(self.host + '/runestone/default/user/login')

        ## fill out the login form ##
        self.driver.find_element_by_id('auth_user_username'). \
            send_keys(self.username)
        self.driver.find_element_by_id('auth_user_password'). \
            send_keys(self.password)

        ## submit the login form ##
        self.driver.find_element_by_css_selector("input[value='Login']"). \
            click()

        ## check that we were redirected to the course this user is registered for ##
        expected_course_url = self.host + "/runestone/static/" + self.course_name
        self.assertIn(expected_course_url, self.driver.current_url,
                      "Not redirected to expected course (%s)." % self.course_name)

        ## check that the user dropdown menu has the email address of the logged in user ##
        # open the menu
        self.driver.find_elements_by_class_name('dropdown-toggle')[2].click()

        # make sure it actually did open
        dropdown_el = self.driver.find_element_by_class_name('open')

        # get the list with the menu items
        search_menu = dropdown_el.find_element_by_class_name('user-menu')

        # get the span with the email address of the logged in user
        span = search_menu.find_element_by_class_name('loggedinuser')

        self.assertEqual(span.text, self.email,
                         "Email address of current user is not visible in user "
                         "navbar menu: expected %s, got %s" % (self.email, span.text))


    def logout(self):
        '''
        Verify that we can successfully log out
        '''

        self.driver.get(self.host + '/runestone/default/user/logout')

        ## check that the "Logged out" flash is visible
        try:
            flash_div = self.driver.find_element_by_class_name('flash')
            self.assertIn("Logged out", flash_div.text, "Logging out failed! Flash DIV had wrong text.")
        except NoSuchElementException:
            self.assertRaises(RuntimeError("Logging out failed! Could not find flash DIV."))

    def profile(self):
        '''
        Make sure we can navigate to the profile page and that the correct course name
        is displayed
        '''
        self.driver.get(self.host + '/runestone/default/user/profile')

        found_course_name = self.driver.find_element_by_id('auth_user_course_id').get_attribute('value')
        self.assertIn(self.course_name, found_course_name,
                      "Wrong course name displayed in user profile page: \
             expected %s, got %s" % (self.course_name, found_course_name))

    def build_new_course_from_existing_course(self):
        ''' build a new course from an existing course (thinkcspy) '''
        new_course_name = generate_name()

        self.driver.get(self.host + "/runestone/designer")

        self.driver.find_element_by_name('projectname').send_keys(new_course_name)
        self.driver.find_element_by_name('projectdescription').send_keys('a new project')

        self.driver.find_element_by_css_selector("input[value='thinkcspy']").click()

        self.driver.find_element_by_css_selector("input[value='Submit']").click()

        # wait up to a minute for the new course to be created
        WebDriverWait(self.driver, 60) \
            .until(EC.text_to_be_present_in_element((By.TAG_NAME, "body"), 'Your course is ready'))

        self.course_name = new_course_name # user account is now linked with the new course

    def save_load_activecode(self):
        ''' Test that saving and then re-loading an activecode works '''
        self.driver.get(self.host + "/runestone/static/overview/overview.html")

        save_b = self.driver.find_element_by_id('codeexample1_saveb')

        expected_text = 'print("My first program adds two numbers, 2 and 3:")\nprint(2 + 3)\n'
        js = "return cm_editors.codeexample1_code.getValue();"
        actual_text = str(self.driver.execute_script(js))

        self.assertTrue(expected_text == actual_text)

        js = "cm_editors.codeexample1_code.setValue('print(\"Hello, world\")')"
        self.driver.execute_script(js)

        save_b.click()
        time.sleep(2) # give the ajax call some time

        self.driver.refresh()

        load_b = self.driver.find_element_by_id('codeexample1_loadb')
        load_b.click()
        time.sleep(2) # give the ajax call some time

        expected_text = 'print(\"Hello, world\")'
        js = "return cm_editors.codeexample1_code.getValue();"
        actual_text = str(self.driver.execute_script(js))

        self.assertTrue(expected_text == actual_text,
                        "Loading saved code failed! Expected '%s', found '%s'"
                        % (expected_text, actual_text))


