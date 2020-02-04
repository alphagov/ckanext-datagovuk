# Known issues migrating to 2.8

## Style/layout

- breadcrumb font size smaller by 2px
- buttons don't have a `background-image` set for the gradient effect
- form fields are not in line with labels
- all form fields are full width due to the introduction of the `form-control`
class on the `<input>` tag
- validation error blocks aren't in line with related form field

## Form Image URL field
This field should have the ability of adding the image by url or upload. The
javascript isn't loading the `Data` field as expected, and the upload field
appears hidden on the page. This looks like an identical issue to the organogram
dataset upload field, see below.

## Creating a new resource

### Format autocomplete feature not working
In step two of creating a dataset (/dataset/new-resource), it should have the
ability of autocompleting the `format` field when populated. It is currently
showing a static form field - see https://github.com/alphagov/ckan/blob/master/ckan/templates/package/snippets/resource_form.html#L38-L44
The script used to load the field is https://github.com/alphagov/ckan/blob/master/ckan/public/base/javascript/modules/autocomplete.js

### Organogram dataset upload form

In step two of creating a dataset (/dataset/new-resource), it should have the
ability of adding the resource by url or upload. The javascript isn't loading the
`Data` field as expected, and the upload field appears hidden on the page - see
https://github.com/alphagov/ckan/blob/master/ckan/templates/package/snippets/resource_form.html#L23-L26
The script used to load the field is https://github.com/alphagov/ckan/blob/master/ckan/public/base/javascript/modules/image-upload.js
