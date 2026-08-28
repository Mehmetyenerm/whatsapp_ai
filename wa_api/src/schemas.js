export const opts = {
    schema: {
        response: {
            '2xx': {
                type: 'object',
                properties: {
                    hello: {
                        type: 'string'
                    }
                }
            }
        }
    }
}

export const optsFile = {
    schema: {
        description: 'WhatsApp dosya (resim ve ses) mesajı gönderir',
        tags: ['Message'],
        body: {
            type: 'object',
            required: ['to', 'filePath'],
            properties: {
                to: {
                    type: 'integer'
                },
                filePath: {
                    type: 'string'
                }
            }
        },
        response: {
            200: {
                type: 'object',
                properties: {
                    success: {
                        type: 'boolean'
                    },
                    messageId: {
                        type: 'string'
                    }
                }
            },
            400: {
                type: 'object',
                properties: {
                    error: {
                        type: 'string'
                    }
                }
            },
            500: {
                type: 'object',
                properties: {
                    success: {
                        type: 'boolean'
                    },
                    error: {
                        type: 'string'
                    }
                }
            }
        }
    }
}

export const optsText = {
    schema: {
        description: 'WhatsApp text mesajı gönderir',
        tags: ['Message'],
        body: {
            type: 'object',
            required: ['to', 'message'],
            properties: {
                to: {
                    type: 'integer'
                },
                message: {
                    type: 'string'
                }
            }
        },
        response: {
            200: {
                type: 'object',
                properties: {
                    success: {
                        type: 'boolean'
                    },
                    messageId: {
                        type: 'string'
                    }
                }
            },
            400: {
                type: 'object',
                properties: {
                    error: {
                        type: 'string'
                    }
                }
            },
            500: {
                type: 'object',
                properties: {
                    success: {
                        type: 'boolean'
                    },
                    error: {
                        type: 'string'
                    }
                }
            }
        }
    }
}

export const optsUser = {
    schema: {
        description: 'WhatsApp logout istegi gonderir' ,
        tags: ['User'],
    }
}
