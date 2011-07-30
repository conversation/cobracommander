template = """
# Commands required to run the build
[steps]
%build_step%

# What to do on build pass
[pass]
echo "I win at the coding"

# What to do on build fail
[fail]
echo "I lose"
"""

build_steps = {
  rails: "bundle exec rake",
  django: "manage.py test"
}

$ ->
  $("input[type=radio]").change ->
    selected = $("input[type=radio]:checked").val()
    $("textarea").val template.replace("%build_step%", build_steps[selected])
  $("input[type=radio]").first().click()
