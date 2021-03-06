from collections import OrderedDict

from flexmock import flexmock
from nose.tools import assert_raises

from atticmatic import config as module


def test_option_should_create_config_option():
    option = module.option('name', bool, required=False)

    assert option == module.Config_option('name', bool, False)


def test_option_should_create_config_option_with_defaults():
    option = module.option('name')

    assert option == module.Config_option('name', str, True)


def test_validate_configuration_format_with_valid_config_should_not_raise():
    parser = flexmock()
    parser.should_receive('sections').and_return(('section', 'other'))
    parser.should_receive('options').with_args('section').and_return(('stuff',))
    parser.should_receive('options').with_args('other').and_return(('such',))
    config_format = (
        module.Section_format(
            'section',
            options=(
                module.Config_option('stuff', str, required=True),
            ),
        ),
        module.Section_format(
            'other',
            options=(
                module.Config_option('such', str, required=True),
            ),
        ),
    )

    module.validate_configuration_format(parser, config_format)


def test_validate_configuration_format_with_missing_section_should_raise():
    parser = flexmock()
    parser.should_receive('sections').and_return(('section',))
    config_format = (
        module.Section_format('section', options=()),
        module.Section_format('missing', options=()),
    )

    with assert_raises(ValueError):
        module.validate_configuration_format(parser, config_format)


def test_validate_configuration_format_with_extra_section_should_raise():
    parser = flexmock()
    parser.should_receive('sections').and_return(('section', 'extra'))
    config_format = (
        module.Section_format('section', options=()),
    )

    with assert_raises(ValueError):
        module.validate_configuration_format(parser, config_format)


def test_validate_configuration_format_with_missing_required_option_should_raise():
    parser = flexmock()
    parser.should_receive('sections').and_return(('section',))
    parser.should_receive('options').with_args('section').and_return(('option',))
    config_format = (
        module.Section_format(
            'section',
            options=(
                module.Config_option('option', str, required=True),
                module.Config_option('missing', str, required=True),
            ),
        ),
    )

    with assert_raises(ValueError):
        module.validate_configuration_format(parser, config_format)


def test_validate_configuration_format_with_missing_optional_option_should_not_raise():
    parser = flexmock()
    parser.should_receive('sections').and_return(('section',))
    parser.should_receive('options').with_args('section').and_return(('option',))
    config_format = (
        module.Section_format(
            'section',
            options=(
                module.Config_option('option', str, required=True),
                module.Config_option('missing', str, required=False),
            ),
        ),
    )

    module.validate_configuration_format(parser, config_format)


def test_validate_configuration_format_with_extra_option_should_raise():
    parser = flexmock()
    parser.should_receive('sections').and_return(('section',))
    parser.should_receive('options').with_args('section').and_return(('option', 'extra'))
    config_format = (
        module.Section_format(
            'section',
            options=(module.Config_option('option', str, required=True),),
        ),
    )

    with assert_raises(ValueError):
        module.validate_configuration_format(parser, config_format)


def test_parse_section_options_should_return_section_options():
    parser = flexmock()
    parser.should_receive('get').with_args('section', 'foo').and_return('value')
    parser.should_receive('getint').with_args('section', 'bar').and_return(1)
    parser.should_receive('has_option').with_args('section', 'foo').and_return(True)
    parser.should_receive('has_option').with_args('section', 'bar').and_return(True)

    section_format = module.Section_format(
        'section',
        (
            module.Config_option('foo', str, required=True),
            module.Config_option('bar', int, required=True),
        ),
    )

    config = module.parse_section_options(parser, section_format)

    assert config == OrderedDict(
        (
            ('foo', 'value'),
            ('bar', 1),
        )
    )


def insert_mock_parser():
    parser = flexmock()
    parser.should_receive('readfp')
    flexmock(module).open = lambda filename: None
    flexmock(module).ConfigParser = parser

    return parser


def test_parse_configuration_should_return_section_configs():
    parser = insert_mock_parser()
    mock_module = flexmock(module)
    mock_module.should_receive('validate_configuration_format').with_args(
        parser, module.CONFIG_FORMAT,
    ).once()
    mock_section_configs = (flexmock(), flexmock())

    for section_format, section_config in zip(module.CONFIG_FORMAT, mock_section_configs):
        mock_module.should_receive('parse_section_options').with_args(
            parser, section_format,
        ).and_return(section_config).once()

    section_configs = module.parse_configuration('filename')

    assert section_configs == mock_section_configs
